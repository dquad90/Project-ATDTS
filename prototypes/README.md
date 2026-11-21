# Progressive Development Prototypes (Phases 1–12)

This folder archives the evolutionary prototypes and early milestone test scripts developed during the iterative construction of the **Automated Tower Defence Target Selector (`PROJECT-Ai`)**:

* **`test1.py` – Phase 1:** Initial Pygame canvas and basic entity primitives.
* **`test2.py` – Phase 2:** Basic kinematic movement and straight-line enemy navigation.
* **`test3.py` – Phase 3:** Static single-tower range detection and simple radial proximity checks.
* **`test4.py` – Phase 4:** Nearest-enemy target locking and rudimentary projectile dispatch.
* **`test5.py` – Phase 5:** Multi-tower setup and baseline hit-point damage resolution.
* **`test6.py` – Phase 6:** Base Town Hall introduction and collision detection.
* **`test7.py` – Phase 7:** Enemy health bars and variable movement speed attributes.
* **`test8.py` – Phase 8:** First prototype of multi-attribute threat scoring logic.
* **`test9.py` – Phase 9:** Multi-archetype enemy profiles (Scout, Tank, Boss, Swarm).
* **`test10.py` – Phase 10:** AoE Mortar splash damage, cluster density calculations, and floating combat text.
* **`test11.py` – Phase 11:** Headless simulation loop testing and preliminary wave generators.
* **`test12.py` – Phase 12:** Pre-modular architecture prototype before splitting into `core/`, `gui/`, and `scenarios/`.

The production implementation resides in [`main.py`](../main.py) and the [`core/`](../core/) package.
