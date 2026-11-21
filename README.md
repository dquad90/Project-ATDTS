# Automated Tower Defence Target Selector (PROJECT-Ai)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Pygame 2.5+](https://img.shields.io/badge/pygame-2.5+-green.svg)](https://www.pygame.org/)
[![NumPy](https://img.shields.io/badge/numpy-1.24+-orange.svg)](https://numpy.org/)
[![License: Academic](https://img.shields.io/badge/License-Academic-lightgrey.svg)](LICENSE)

A 2D base-defence simulation developed with **Python**, **Pygame**, and **NumPy**, implementing an intelligent **Utility-Based AI Agent** for defensive target selection. Inspired by *Clash of Clans*–style base defence, this project demonstrates why fixed targeting heuristics (such as nearest-enemy selection) fail against complex multi-attribute raids and how a utility-based decision model dynamically isolates and neutralizes the greatest battlefield threat.

---

## 🏛️ System Architecture

This project strictly adheres to the 7-stage architecture pipeline and PEAS specification defined in the Project Proposal:

```
┌────────────────────────────────────────────────────────┐
│                   Enemy Detection                      │
│        Filter enemies within range: D <= D_MAX         │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│               Collect Enemy Attributes                 │
│         Extract: AP, SPD, HP, Position, D              │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│            Threat / Utility Calculation                │
│    NumPy Vector Dot-Product Multi-Attribute Scoring    │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│             Compare All Detected Enemies               │
│          Sort candidates by utility score desc         │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│            Select Highest-Priority Target              │
│                 e* = argmax U(enemy)                   │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│                     Aim & Attack                       │
│    Actuator Dispatch: Cannon Rotation & Projectile     │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│      Update Game State (Recalculated Target Loop)      │
│      Dynamic Retargeting on tick / health change       │
└────────────────────────────────────────────────────────┘
```

---

## 🧮 Utility Threat Scoring Formula

Every simulation frame, the sensor module measures Euclidean distance $D = \|\mathbf{p}_{\text{enemy}} - \mathbf{p}_{\text{tower}}\|_2$ using NumPy vector operations and evaluates all candidate enemies within sensor range ($D \le D_{\text{MAX}}$):

$$\text{score} = (w_{\text{AP}} \cdot \text{AP}) + (w_{\text{SPD}} \cdot \text{SPD}) + \left(w_{\text{DIST\_PROX}} \cdot \left(1 - \frac{D}{D_{\text{MAX}}}\right) \cdot 100\right) + (w_{\text{HP}} \cdot \text{HP}) + (w_{\text{cluster}} \cdot \text{ClusterCount})$$

### Specialized Defensive Tower Personalities
1. **Standard Tower**: Balanced baseline implementing default report multipliers:
   $$w_{\text{AP}} = 2.0, \quad w_{\text{SPD}} = 1.5, \quad w_{\text{DIST\_PROX}} = 1.0, \quad w_{\text{HP}} = 0.5$$
2. **Artillery Tower**: Heavy siege threat focus prioritizing devastating attack power and armor:
   $$w_{\text{AP}} = 3.0, \quad w_{\text{SPD}} = 0.5, \quad w_{\text{DIST\_PROX}} = 1.0, \quad w_{\text{HP}} = 1.5$$
3. **Defender Tower**: High-proximity perimeter guardian intercepting close breaches:
   $$w_{\text{DIST\_PROX}} = 5.0, \quad w_{\text{AP}} = 1.0, \quad w_{\text{SPD}} = 1.0, \quad w_{\text{HP}} = 0.2$$
4. **Mortar Tower**: Cluster density evaluation delivering AoE splash damage to dense crowds:
   $$w_{\text{cluster}} = 15.0, \quad w_{\text{AP}} = 1.0, \quad w_{\text{SPD}} = -1.0, \quad w_{\text{DIST\_PROX}} = 1.0, \quad \text{Splash Radius} = 105\text{px}$$

---

## 🔍 Explainable AI (XAI) Inspector (Press `TAB`)

The simulation features an interactive **Explainable AI Inspector** that makes the agent's decision-making 100% transparent:
* **Candidate Threat Matrix Table**: Displays all enemies in range with raw $AP, SPD, Dist, Prox, HP$, and weighted total scores.
* **Component Score Breakdown**: Explains how each attribute contributed to the total score.
* **Natural-Language Rationale**: Outputs clear semantic justifications (e.g., *"Prioritized high-threat Boss E-03 over closer Scout E-01 due to massive attack power (+280 utility)"*).
* **Live AI Weight Tuning**: Adjust $w_{\text{AP}}$, $w_{\text{SPD}}$, $w_{\text{PROX}}$, $w_{\text{HP}}$ using on-screen steppers in real time to witness instant target reallocation.
* **Live Strategy Switcher**: Toggle any tower between `Utility-Based AI`, `Nearest Enemy`, `Highest AP`, `Lowest HP`, and `Highest HP`.

---

## ⚔️ Dual Arena Comparison Mode (Press `C`)

Experience the core research hypothesis in real time with the **Split-Screen Dual Arena**:
* **Left Battlefield**: All towers run the classical **Nearest-Enemy Baseline Heuristic**.
* **Right Battlefield**: All towers run the proposed **Utility-Based AI Agent**.
* **Mirrored Waves**: Identical enemy spawns approach both bases simultaneously.
* **Live Scoreboard**: Tracks Base HP retention, kill rates, and damage prevented side-by-side.

---

## 🎯 Tactical Test Scenarios (Objective 5)

Press keys `1` through `5` or click the **SCENARIOS** button to run curated tactical scenarios:
1. **Scenario 1: The Decoy Rush** — Low-threat Scouts rush close to the tower while a deadly Boss approaches behind. Proves Nearest-Enemy fails while Utility AI succeeds!
2. **Scenario 2: Fast Swarm Rush** — 10 high-speed runners converge from all directions, testing speed and proximity defense.
3. **Scenario 3: Heavy Vanguard** — Armored Tanks lead an assault ahead of an Overlord Boss.
4. **Scenario 4: Cluster Incursion** — Dense troop formation demonstrating Mortar AoE cluster targeting.
5. **Scenario 5: Dynamic Retargeting** — Wounded units and fresh bosses demonstrating mid-battle target reallocation.
6. **Key 6 / Button**: Endless procedural wave survival with scaling difficulty.

---

## 🕹️ Controls & Hotkeys

| Key / Input | Action |
| :--- | :--- |
| **TAB** | Toggle Explainable AI (XAI) Candidate Inspector |
| **Drag Title Bar** | Move the Explainable AI window anywhere on screen |
| **Drag Bottom-Right Handle (◢)** | Resize the Explainable AI window width and height |
| **FIT Button / Double-Click Title** | Auto-fit window height to content (eliminates empty voids) |
| **C** | Toggle Split-Screen Dual Arena Mode (Nearest vs Utility AI) |
| **SPACE** | Toggle Pause / Resume |
| **T** | Cycle Targeting Strategy for selected tower |
| **1 – 5** | Instant Load Test Scenarios 1 to 5 |
| **6** | Return to Endless Procedural Wave Defense |
| **M** | Toggle Sound Effects (SFX Mute / Unmute) |
| **W** | Call next wave early during intermission |
| **R** | Instant Restart after game over |
| **Mouse Click** | Click UI buttons, sliders, or click a tower on the field to inspect it |

---

## 🚀 Installation & Running

### 1. Requirements
Ensure Python 3.10 or newer is installed.

```bash
cd PROJECT-Ai
pip install -r requirements.txt
```

### 2. Launch Interactive Simulation
```bash
python main.py
```

### 3. Run Automated Benchmark Suite (Objective 5)
```bash
python benchmark.py
```
Outputs ASCII comparison tables to the console and generates `BENCHMARK_REPORT.md` and `benchmark_results.json`.

### 4. Run Unit & PEAS Test Suite
```bash
python -m unittest tests/test_simulation.py
```

---

## 📋 Course & Academic Information
* **Course:** CSE 3202 — Artificial Intelligence Sessional
* **Project Title:** Automated Tower Defence Target Selector
* **Team Members:**
  * Md Modabbir Hossen Asif (ID: 0802410205101010)
  * Darunnaim Sindid (ID: 08024102051026)
* **Instructor:** Zahim Hassan
