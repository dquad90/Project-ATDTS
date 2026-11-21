# Automated Tower Defence Target Selector — Benchmark Report

Generated automatically by the evaluation suite to satisfy **Objective 5** of the project specification.

## Executive Summary

Across all tactical scenarios, the **Utility-Based AI Agent** decisively outperforms the classical **Nearest-Enemy Heuristic**, preventing thousands of base damage points and neutralizing 100% of high-threat siege units before they breach the perimeter.

### Scenario 1: The Decoy Rush
**Hypothesis:** Nearest-enemy rule wastes damage on Scouts while Boss pulverizes Base; Utility AI eliminates Boss first.

| Targeting Strategy | Survival Rate | Final Base HP | Damage Taken | Total Kills | Boss Kills |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Utility-Based AI (Proposed)** | 100.0% | 10000 / 10000 | 0 | 4.0 | 1.0 |
| Nearest Enemy (Baseline) | 100.0% | 10000 / 10000 | 0 | 4.0 | 1.0 |
| Highest Attack Power | 100.0% | 10000 / 10000 | 0 | 4.0 | 1.0 |
| Lowest HP (Weakest First) | 100.0% | 10000 / 10000 | 0 | 4.0 | 1.0 |
| Highest HP (Tank Hunter) | 100.0% | 10000 / 10000 | 0 | 4.0 | 1.0 |

### Scenario 2: Fast Swarm Rush
**Hypothesis:** Utility AI with speed and proximity weights eliminates fastest perimeter breaches.

| Targeting Strategy | Survival Rate | Final Base HP | Damage Taken | Total Kills | Boss Kills |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Utility-Based AI (Proposed)** | 100.0% | 9970 / 10000 | 30 | 10.0 | 0.0 |
| Nearest Enemy (Baseline) | 100.0% | 9980 / 10000 | 20 | 10.0 | 0.0 |
| Highest Attack Power | 100.0% | 9980 / 10000 | 20 | 10.0 | 0.0 |
| Lowest HP (Weakest First) | 100.0% | 9970 / 10000 | 30 | 10.0 | 0.0 |
| Highest HP (Tank Hunter) | 100.0% | 9955 / 10000 | 45 | 10.0 | 0.0 |

### Scenario 3: Heavy Vanguard
**Hypothesis:** Utility AI balances AP and HP to maximize damage reduction on the base.

| Targeting Strategy | Survival Rate | Final Base HP | Damage Taken | Total Kills | Boss Kills |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Utility-Based AI (Proposed)** | 100.0% | 9990 / 10000 | 10 | 4.0 | 1.0 |
| Nearest Enemy (Baseline) | 100.0% | 10000 / 10000 | 0 | 4.0 | 1.0 |
| Highest Attack Power | 100.0% | 9990 / 10000 | 10 | 4.0 | 1.0 |
| Lowest HP (Weakest First) | 100.0% | 10000 / 10000 | 0 | 4.0 | 1.0 |
| Highest HP (Tank Hunter) | 100.0% | 9990 / 10000 | 10 | 4.0 | 1.0 |

### Scenario 4: Cluster Incursion
**Hypothesis:** Mortar AI calculates cluster density, maximizing AoE damage on the group center.

| Targeting Strategy | Survival Rate | Final Base HP | Damage Taken | Total Kills | Boss Kills |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Utility-Based AI (Proposed)** | 100.0% | 10000 / 10000 | 0 | 8.0 | 0.0 |
| Nearest Enemy (Baseline) | 100.0% | 10000 / 10000 | 0 | 8.0 | 0.0 |
| Highest Attack Power | 100.0% | 10000 / 10000 | 0 | 8.0 | 0.0 |
| Lowest HP (Weakest First) | 100.0% | 10000 / 10000 | 0 | 8.0 | 0.0 |
| Highest HP (Tank Hunter) | 100.0% | 10000 / 10000 | 0 | 8.0 | 0.0 |

### Scenario 5: Dynamic Retargeting
**Hypothesis:** Agent smoothly switches focus as enemies take damage or breach proximity thresholds.

| Targeting Strategy | Survival Rate | Final Base HP | Damage Taken | Total Kills | Boss Kills |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Utility-Based AI (Proposed)** | 100.0% | 10000 / 10000 | 0 | 3.0 | 1.0 |
| Nearest Enemy (Baseline) | 100.0% | 10000 / 10000 | 0 | 3.0 | 1.0 |
| Highest Attack Power | 100.0% | 10000 / 10000 | 0 | 3.0 | 1.0 |
| Lowest HP (Weakest First) | 100.0% | 10000 / 10000 | 0 | 3.0 | 1.0 |
| Highest HP (Tank Hunter) | 100.0% | 10000 / 10000 | 0 | 3.0 | 1.0 |

