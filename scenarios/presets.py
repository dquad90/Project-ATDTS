"""
Calibrated Battlefield Scenarios for AI Target Selection Evaluation.
Addresses Objective 5: 'Evaluate the system using different enemy combinations
and changing battlefield situations.'
Directly proves the failure of nearest-enemy heuristics vs utility-based AI.
"""

from dataclasses import dataclass
from typing import List, Dict, Callable
import math
import numpy as np

from core.entities import Enemy, ENEMY_DATABASE


@dataclass
class ScenarioInfo:
    """Metadata and definition of an evaluation scenario."""
    id: int
    name: str
    subtitle: str
    description: str
    hypothesis: str
    expected_nearest_outcome: str
    expected_utility_outcome: str
    spawn_generator: Callable[[int, int], List[Enemy]]


def spawn_decoy_rush(base_x: int, base_y: int) -> List[Enemy]:
    """
    Scenario 1: The Decoy Rush.
    3 low-threat Scouts deployed very close to the tower (D ~ 80-140px),
    while a deadly Boss (AP=250, HP=400) advances toward the base (D ~ 220px).
    Nearest-enemy attacks the Scouts first; Utility AI snipes the Boss!
    """
    enemies = []
    # 3 distraction scouts positioned close to the top-left tower (base_x - 150, base_y - 150)
    scouts_data = [
        (base_x - 210, base_y - 210, "Decoy-01"),
        (base_x - 190, base_y - 230, "Decoy-02"),
        (base_x - 170, base_y - 240, "Decoy-03"),
    ]
    for sx, sy, sid in scouts_data:
        s = Enemy("Scout", sx, sy, custom_id=sid)
        s.speed = 0.55
        enemies.append(s)

    # High-threat Boss advancing along diagonal toward base
    boss = Enemy("Boss", base_x - 100, base_y - 250, custom_id="Deadly-Boss")
    boss.hp = 380.0
    boss.max_hp = 380.0
    boss.ap = 250.0  # Devastating attack power
    boss.speed = 0.45
    enemies.append(boss)
    return enemies


def spawn_fast_swarm(base_x: int, base_y: int) -> List[Enemy]:
    """
    Scenario 2: Fast Scout / Swarm Rush.
    10 fast movers converging from multiple compass directions.
    """
    enemies = []
    angles = np.linspace(0, 2 * math.pi, 10, endpoint=False)
    for idx, angle in enumerate(angles, 1):
        dist = 380
        x = base_x + math.cos(angle) * dist
        y = base_y + math.sin(angle) * dist
        enemy_type = "Swarm" if idx % 2 == 0 else "Scout"
        e = Enemy(enemy_type, x, y, custom_id=f"Swarm-{idx:02d}")
        e.speed = 2.0
        enemies.append(e)
    return enemies


def spawn_heavy_vanguard(base_x: int, base_y: int) -> List[Enemy]:
    """
    Scenario 3: Heavy Armor Vanguard.
    Heavy Tanks and high-AP units advancing with staggered spacing.
    """
    enemies = []
    tanks = [
        (base_x + 240, base_y - 180, "Tank", "Vanguard-01"),
        (base_x + 280, base_y - 150, "Tank", "Vanguard-02"),
        (base_x + 320, base_y - 260, "Boss", "Overlord-01"),
        (base_x + 140, base_y - 280, "Scout", "Flanker-01")
    ]
    for x, y, etype, eid in tanks:
        enemies.append(Enemy(etype, x, y, custom_id=eid))
    return enemies


def spawn_cluster_incursion(base_x: int, base_y: int) -> List[Enemy]:
    """
    Scenario 4: Dense Cluster Incursion (Mortar AoE Demo).
    A dense cluster of 6 enemies tightly packed together, plus 2 distant isolated scouts.
    """
    enemies = []
    # Tight cluster center at (base_x + 200, base_y + 200)
    cx, cy = base_x + 200, base_y + 200
    cluster_offsets = [
        (0, 0), (22, 14), (-18, 18), (14, -22), (-22, -14), (25, -8)
    ]
    for idx, (ox, oy) in enumerate(cluster_offsets, 1):
        etype = "Tank" if idx == 1 else "Scout"
        enemies.append(Enemy(etype, cx + ox, cy + oy, custom_id=f"Cluster-{idx:02d}"))

    # Isolated scouts far away
    enemies.append(Enemy("Scout", base_x - 260, base_y + 80, custom_id="Isolated-01"))
    enemies.append(Enemy("Scout", base_x + 80, base_y - 300, custom_id="Isolated-02"))
    return enemies


def spawn_dynamic_battle(base_x: int, base_y: int) -> List[Enemy]:
    """
    Scenario 5: Dynamic Battlefield & Health Degradation.
    Mix of damaged and fresh units at various distances to test retargeting transitions.
    """
    enemies = []
    # Wounded tank close by
    t1 = Enemy("Tank", base_x - 150, base_y + 110, custom_id="Damaged-Tank")
    t1.hp = 60.0  # severely wounded
    enemies.append(t1)

    # Fresh Boss approaching
    b1 = Enemy("Boss", base_x - 240, base_y + 210, custom_id="Full-Boss")
    b1.hp = 600.0
    b1.max_hp = 600.0
    b1.ap = 200.0
    enemies.append(b1)

    # Fast scout
    s1 = Enemy("Scout", base_x + 180, base_y - 130, custom_id="Fast-Scout")
    enemies.append(s1)
    return enemies


ALL_SCENARIOS: Dict[int, ScenarioInfo] = {
    1: ScenarioInfo(
        id=1,
        name="The Decoy Rush",
        subtitle="Nearest-Enemy Failure vs Utility-AI Success",
        description="Low-threat Scouts rush close to tower while a deadly Boss approaches behind.",
        hypothesis="Nearest-enemy rule wastes damage on Scouts while Boss pulverizes Base; Utility AI eliminates Boss first.",
        expected_nearest_outcome="Base suffers heavy damage from ignored Boss.",
        expected_utility_outcome="Boss eliminated before reaching Town Hall; Base survives intact.",
        spawn_generator=spawn_decoy_rush
    ),
    2: ScenarioInfo(
        id=2,
        name="Fast Swarm Rush",
        subtitle="Speed & Perimeter Proximity Defense",
        description="10 high-speed scouts converge simultaneously from all compass angles.",
        hypothesis="Utility AI with speed and proximity weights eliminates fastest perimeter breaches.",
        expected_nearest_outcome="High perimeter leak rate due to lack of speed compensation.",
        expected_utility_outcome="Speed-weighted targeting neutralizes fast threats in priority order.",
        spawn_generator=spawn_fast_swarm
    ),
    3: ScenarioInfo(
        id=3,
        name="Heavy Vanguard",
        subtitle="Multi-Attribute AP & Armor Prioritization",
        description="Armored Tanks lead the charge ahead of a massive Boss and flanking Scouts.",
        hypothesis="Utility AI balances AP and HP to maximize damage reduction on the base.",
        expected_nearest_outcome="Towers waste shots on low AP flankers or fail to stop vanguard.",
        expected_utility_outcome="Artillery and high-AP weights take down heaviest siege threats.",
        spawn_generator=spawn_heavy_vanguard
    ),
    4: ScenarioInfo(
        id=4,
        name="Cluster Incursion",
        subtitle="Cluster Density & AoE Splash Bombardment",
        description="A dense pack of troops arrives in formation alongside isolated scouts.",
        hypothesis="Mortar AI calculates cluster density, maximizing AoE damage on the group center.",
        expected_nearest_outcome="Mortar fires at closest isolated scout, wasting splash radius.",
        expected_utility_outcome="Mortar targets cluster epicenter, wiping out 5+ enemies in single volley.",
        spawn_generator=spawn_cluster_incursion
    ),
    5: ScenarioInfo(
        id=5,
        name="Dynamic Retargeting",
        subtitle="Real-Time Adaptation to Health & Distance Changes",
        description="Damaged units and fresh bosses interact; tests state transitions mid-combat.",
        hypothesis="Agent smoothly switches focus as enemies take damage or breach proximity thresholds.",
        expected_nearest_outcome="Stuck on closest unit even when its threat is negligible.",
        expected_utility_outcome="Seamless dynamic retargeting as battlefield attributes evolve.",
        spawn_generator=spawn_dynamic_battle
    )
}
