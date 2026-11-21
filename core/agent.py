"""
Utility-Based AI Agent & Threat Evaluation Engine.
Implements the 7-stage Architecture Pipeline from the Project Specification:
  1. Enemy Detection (Partially observable sensor boundary D <= D_MAX)
  2. Collect Enemy Attributes (AP, SPD, HP, Position, Distance to Tower, Proximity)
  3. Threat/Utility Calculation (Vectorized NumPy dot product)
  4. Compare All Detected Enemies (Ranking & Sorting)
  5. Select Highest-Priority Target (argmax U(e))
  6. Aim & Attack Actuator Dispatch
  7. Update Game State (Continuous dynamic retargeting loop)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
import numpy as np


class TargetingStrategy(Enum):
    """Targeting heuristics and agent architectures supported by towers."""
    UTILITY_AI = "Utility-Based AI (Proposed)"
    NEAREST_ENEMY = "Nearest Enemy (Baseline)"
    HIGHEST_AP = "Highest Attack Power"
    LOWEST_HP = "Lowest HP (Weakest First)"
    HIGHEST_HP = "Highest HP (Tank Hunter)"
    FASTEST = "Fastest Enemy (Speed Priority)"


@dataclass
class ComponentScores:
    """Detailed breakdown of individual attribute utility contributions."""
    ap_score: float = 0.0
    spd_score: float = 0.0
    dist_prox_score: float = 0.0
    hp_score: float = 0.0
    cluster_score: float = 0.0

    @property
    def total(self) -> float:
        return (
            self.ap_score
            + self.spd_score
            + self.dist_prox_score
            + self.hp_score
            + self.cluster_score
        )


@dataclass
class CandidateEvaluation:
    """Structured telemetry record for a detected enemy candidate."""
    enemy_id: str
    enemy_name: str
    ap: float
    spd: float
    hp: float
    max_hp: float
    distance: float
    proximity: float
    cluster_count: int
    components: ComponentScores
    total_score: float
    rank: int = 1
    is_selected: bool = False
    explanation: str = ""


class UtilityBasedAgent:
    """
    Intelligent Target Selector implementing the Utility-Based Agent model.
    Evaluates multi-attribute threat vectors using vectorized NumPy dot product.
    """

    def __init__(self, weights: Dict[str, float], proximity_scale: float = 100.0):
        """
        Initializes agent with specific priority weights:
          - AP: Attack Power / Threat multiplier
          - SPD: Movement speed multiplier
          - DIST_PROX: Normalized proximity (1 - D/D_MAX) multiplier
          - HP: Health weight multiplier
          - cluster: AoE cluster density multiplier (optional)
          - proximity_scale: Multiplier (default 100.0) scaling normalized (1 - D/D_MAX)
            to parity with AP and HP features as prescribed in Methodology Step 3.
        """
        self.proximity_scale = proximity_scale
        self.weights = {
            'AP': float(weights.get('AP', 2.0)),
            'SPD': float(weights.get('SPD', 1.5)),
            'DIST_PROX': float(weights.get('DIST_PROX', 1.0)),
            'HP': float(weights.get('HP', 0.5)),
            'cluster': float(weights.get('cluster', 0.0))
        }

    def compute_threat_score(
        self,
        ap: float,
        spd: float,
        prox: float,
        hp: float,
        cluster: float = 0.0
    ) -> Tuple[float, ComponentScores]:
        """
        Computes the utility threat score using vectorized NumPy dot product:
        score = (w_AP * AP) + (w_SPD * SPD) + (w_DIST_PROX * (1 - D/D_MAX) * SCALE) + (w_HP * HP) + (w_cluster * cluster)
        """
        # Scale normalized proximity [0, 1] into [0, 100] percentage space for multi-attribute balance
        scaled_prox = prox * self.proximity_scale

        attr_vec = np.array([ap, spd, scaled_prox, hp, cluster], dtype=np.float32)
        weight_vec = np.array([
            self.weights['AP'],
            self.weights['SPD'],
            self.weights['DIST_PROX'],
            self.weights['HP'],
            self.weights['cluster']
        ], dtype=np.float32)

        prod = attr_vec * weight_vec
        comp = ComponentScores(
            ap_score=float(prod[0]),
            spd_score=float(prod[1]),
            dist_prox_score=float(prod[2]),
            hp_score=float(prod[3]),
            cluster_score=float(prod[4])
        )
        total = float(np.sum(prod))
        return total, comp

    def evaluate_all(
        self,
        tower_x: float,
        tower_y: float,
        attack_range: float,
        splash_radius: float,
        enemies: List[Any],
        strategy: TargetingStrategy = TargetingStrategy.UTILITY_AI
    ) -> Tuple[Optional[Any], List[CandidateEvaluation], str]:
        """
        Executes sensor detection, attribute parsing, and target evaluation.
        Returns:
          - best_target: Reference to chosen enemy (or None)
          - candidate_records: Sorted list of CandidateEvaluation objects
          - natural_explanation: Explainable rationale text
        """
        if not enemies:
            return None, [], "No enemies detected on battlefield."

        # Stage 1: Partially Observable Sensor Boundary Filter (D <= attack_range)
        candidates = []
        for enemy in enemies:
            if enemy.hp <= 0:
                continue
            # Euclidean distance using NumPy
            diff = np.array([enemy.x - tower_x, enemy.y - tower_y], dtype=np.float32)
            dist = float(np.linalg.norm(diff))
            if dist <= attack_range:
                candidates.append((enemy, dist))

        if not candidates:
            return None, [], f"Sensors active: No enemies within range ({int(attack_range)}px)."

        # Stage 2 & 3: Attribute Collection & Threat Scoring
        records: List[CandidateEvaluation] = []
        for enemy, dist in candidates:
            # Normalized proximity factor (1 - D / D_MAX)
            prox = max(0.0, 1.0 - (dist / attack_range))

            # Cluster density calculation for AoE weapons
            cluster_count = 0
            if splash_radius > 0 and len(enemies) > 1:
                coords = np.array([[e.x, e.y] for e in enemies if e != enemy and e.hp > 0], dtype=np.float32)
                if len(coords) > 0:
                    target_coord = np.array([enemy.x, enemy.y], dtype=np.float32)
                    dists = np.linalg.norm(coords - target_coord, axis=1)
                    cluster_count = int(np.sum(dists <= splash_radius))

            total_score, comp = self.compute_threat_score(
                ap=enemy.ap,
                spd=enemy.speed,
                prox=prox,
                hp=enemy.hp,
                cluster=float(cluster_count)
            )

            record = CandidateEvaluation(
                enemy_id=enemy.id,
                enemy_name=enemy.name,
                ap=enemy.ap,
                spd=enemy.speed,
                hp=enemy.hp,
                max_hp=enemy.max_hp,
                distance=dist,
                proximity=prox,
                cluster_count=cluster_count,
                components=comp,
                total_score=total_score
            )
            records.append(record)

        # Stage 4 & 5: Strategy-dependent comparison and target isolation
        enemy_map = {e.id: e for e, _ in candidates}

        if strategy == TargetingStrategy.UTILITY_AI:
            # Rank by utility score descending; tie-break by smaller distance
            records.sort(key=lambda r: (r.total_score, -r.distance), reverse=True)

        elif strategy == TargetingStrategy.NEAREST_ENEMY:
            # Baseline: Rank strictly by smallest Euclidean distance D
            records.sort(key=lambda r: r.distance)

        elif strategy == TargetingStrategy.HIGHEST_AP:
            # Greedy Threat: Highest attack power first
            records.sort(key=lambda r: (r.ap, -r.distance), reverse=True)

        elif strategy == TargetingStrategy.LOWEST_HP:
            # Weakest First: Lowest current HP first (finish-off heuristic)
            records.sort(key=lambda r: (r.hp, r.distance))

        elif strategy == TargetingStrategy.HIGHEST_HP:
            # Tank Buster: Highest current HP first
            records.sort(key=lambda r: (r.hp, -r.distance), reverse=True)

        elif strategy == TargetingStrategy.FASTEST:
            # Speed Priority: Fastest enemy first
            records.sort(key=lambda r: (r.spd, -r.distance), reverse=True)

        # Assign ranks and select top candidate
        for rank_idx, record in enumerate(records, start=1):
            record.rank = rank_idx

        best_record = records[0]
        best_record.is_selected = True
        best_target = enemy_map[best_record.enemy_id]

        # Generate Explainable AI Rationale
        explanation = self._build_explanation(best_record, records, strategy)
        best_record.explanation = explanation

        return best_target, records, explanation

    def _build_explanation(
        self,
        winner: CandidateEvaluation,
        all_records: List[CandidateEvaluation],
        strategy: TargetingStrategy
    ) -> str:
        """Constructs an explainable natural-language explanation of the decision."""
        if strategy == TargetingStrategy.UTILITY_AI:
            if len(all_records) == 1:
                return (
                    f"Sole detected threat: {winner.enemy_name} [{winner.enemy_id}] "
                    f"(Score: {winner.total_score:.1f})."
                )

            runner_up = all_records[1]
            # Analyze key deciding factors
            lead = winner.total_score - runner_up.total_score
            if winner.components.ap_score > runner_up.components.ap_score and winner.distance > runner_up.distance:
                return (
                    f"Prioritized high-threat {winner.enemy_name} [{winner.enemy_id}] (AP={winner.ap}, Score={winner.total_score:.1f}) "
                    f"over closer {runner_up.enemy_name} [{runner_up.enemy_id}] (D={int(runner_up.distance)}px) "
                    f"due to massive attack power (+{winner.components.ap_score - runner_up.components.ap_score:.1f} utility)."
                )
            elif winner.components.cluster_score > 0 and winner.cluster_count > runner_up.cluster_count:
                return (
                    f"Selected {winner.enemy_name} [{winner.enemy_id}] at cluster center "
                    f"({winner.cluster_count} adjacent troops in AoE) yielding +{winner.components.cluster_score:.1f} splash bonus."
                )
            elif winner.components.dist_prox_score > runner_up.components.dist_prox_score:
                return (
                    f"Selected {winner.enemy_name} [{winner.enemy_id}] (Score={winner.total_score:.1f}) "
                    f"as imminent breach threat ({int(winner.distance)}px from tower, Proximity={winner.proximity:.2f})."
                )
            else:
                return (
                    f"Selected {winner.enemy_name} [{winner.enemy_id}] with highest utility score {winner.total_score:.1f} "
                    f"(+{lead:.1f} ahead of {runner_up.enemy_name} [{runner_up.enemy_id}])."
                )

        elif strategy == TargetingStrategy.NEAREST_ENEMY:
            return (
                f"[Baseline Nearest] Selected {winner.enemy_name} [{winner.enemy_id}] strictly based on "
                f"closest proximity (D={int(winner.distance)}px), ignoring dangerous distant threats."
            )

        elif strategy == TargetingStrategy.HIGHEST_AP:
            return (
                f"[Greedy AP] Selected {winner.enemy_name} [{winner.enemy_id}] with highest attack power "
                f"(AP={winner.ap}), ignoring proximity."
            )

        elif strategy == TargetingStrategy.LOWEST_HP:
            return (
                f"[Weakest First] Target {winner.enemy_name} [{winner.enemy_id}] with lowest HP "
                f"({int(winner.hp)}/{int(winner.max_hp)}) to maximize quick eliminations."
            )

        elif strategy == TargetingStrategy.HIGHEST_HP:
            return (
                f"[Tank Buster] Focused heaviest armor unit: {winner.enemy_name} [{winner.enemy_id}] "
                f"({int(winner.hp)} HP)."
            )

        elif strategy == TargetingStrategy.FASTEST:
            return (
                f"[Fastest Speed] Intercepting highest speed runner: {winner.enemy_name} [{winner.enemy_id}] "
                f"(SPD={winner.spd:.1f})."
            )

        return f"Target {winner.enemy_name} [{winner.enemy_id}] selected."
