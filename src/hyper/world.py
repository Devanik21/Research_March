"""
world.py — Physical Environment v2.0
======================================
The world the BioHyperAgents inhabit — now with Knowledge Physics.

Resources: food, energy_crystal, knowledge_ore, rare_element
  — distributed via multi-cluster Gaussian noise
  — regenerate slowly; scarce locally after consumption
  — periodic world events (abundance shocks, scarcity zones, anomalies)

Knowledge Field: diffusing scalar field representing "ambient intelligence"
  — agents boost it when they invent
  — diffuses each tick (Gaussian blur)
  — high-field areas boost meta-invention probability

Artifacts: persistent knowledge objects left by agents
  — any agent can absorb another agent's artifacts
  — legacy artifacts persist after death

Global Civilization Memory: autoassociative matrix for world knowledge
  — stores all breakthrough inventions
  — agents can query it for resonance retrieval

Spatial index: grid-based O(1) agent lookup.

Invented by Devanik & Claude (Xylia) — Event Horizon Project
"""

import numpy as np
from typing import Dict, List, Optional, Tuple

from metacognition import K_DIM, CivilizationMemory

# ── Resource types ───────────────────────────────────────────────────────────
N_RESOURCES  = 4
R_FOOD       = 0
R_ENERGY     = 1
R_KNOWLEDGE  = 2
R_RARE       = 3
R_NAMES      = ['Food', 'Energy Crystal', 'Knowledge Ore', 'Rare Element']


class World:
    """
    Toroidal 2-D environment with:
      - Multi-cluster resource fields
      - Knowledge field (diffusing ambient intelligence)
      - Stochastic world events every ~50 ticks
      - Persistent artifact map with idea interference
      - Global CivilizationMemory
      - Efficient agent spatial index
    """

    def __init__(self, size: int = 60, seed: int = 42):
        self.size        = size
        self.rng         = np.random.RandomState(seed % (2**31))
        self.step_count  = 0

        # Resource field  [x, y, resource_type]
        self.resources   = np.zeros((size, size, N_RESOURCES), dtype=np.float32)

        # Knowledge field [x, y] — diffusing ambient intelligence
        self.knowledge_field = np.zeros((size, size), dtype=np.float32)

        # Artifact map: (x, y) → dict
        self.artifacts   : Dict[Tuple[int,int], dict] = {}

        # World-level accumulated knowledge
        self.world_knowledge : Dict[str, dict] = {}

        # Global CivilizationMemory (autoassociative matrix)
        self.global_memory = CivilizationMemory(dim=K_DIM, eta=0.04)

        # World event log
        self.events : List[dict] = []

        # Agent spatial grid: (x, y) → list of agent objects
        self._grid : Dict[Tuple[int,int], list] = {}

        self._init_resources()

    # ── Initialisation ───────────────────────────────────────────────────────

    def _init_resources(self):
        """Gaussian cluster resource placement — rich pockets + background noise."""
        for r in range(N_RESOURCES):
            n_clusters = self.rng.randint(4, 10)
            for _ in range(n_clusters):
                cx   = self.rng.randint(5, self.size - 5)
                cy   = self.rng.randint(5, self.size - 5)
                rad  = self.rng.randint(4, 15)
                inten = self.rng.uniform(1.0, 5.5)
                for x in range(max(0, cx-rad), min(self.size, cx+rad)):
                    for y in range(max(0, cy-rad), min(self.size, cy+rad)):
                        d = np.sqrt((x-cx)**2 + (y-cy)**2)
                        self.resources[x, y, r] += float(
                            inten * np.exp(-d / (rad / 2.0))
                        )

        # Background noise
        self.resources += (self.rng.rand(self.size, self.size, N_RESOURCES)
                           .astype(np.float32) * 0.3)
        self.resources  = np.clip(self.resources, 0.0, 8.0)

    # ── Spatial index ────────────────────────────────────────────────────────

    def register_agents(self, agents: list) -> None:
        """Rebuild spatial grid from alive agents (called each tick)."""
        self._grid = {}
        for a in agents:
            if a.alive:
                key = (int(a.x), int(a.y))
                self._grid.setdefault(key, []).append(a)

    def get_agents_near(self, x: int, y: int, radius: int = 5) -> list:
        """Return all agents within Chebyshev radius (fast grid lookup)."""
        result = []
        r2 = radius * radius
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if dx * dx + dy * dy <= r2:
                    key = ((x + dx) % self.size, (y + dy) % self.size)
                    result.extend(self._grid.get(key, []))
        return result

    # ── Physics tick ─────────────────────────────────────────────────────────

    def step(self) -> None:
        """World physics: regeneration + knowledge diffusion + events."""
        self.step_count += 1

        # Slow regeneration (exponential, capped)
        regen = self.rng.exponential(0.0018, self.resources.shape).astype(np.float32)
        self.resources += regen
        self.resources  = np.clip(self.resources, 0.0, 8.0)

        # Knowledge field diffusion (simple 3×3 Gaussian blur + decay)
        self._diffuse_knowledge_field()

        # Idea interference patterns
        self._compute_interference()

        # World events every ~50 ticks
        if self.step_count % 50 == 0:
            self._world_event()

    def _diffuse_knowledge_field(self):
        """
        Gaussian diffusion of the knowledge field.
        Each cell spreads to neighbors; global decay factor applied.
        """
        kf = self.knowledge_field
        # Simple 3×3 averaging kernel (toroidal boundary)
        new_kf = np.zeros_like(kf)
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                new_kf += np.roll(np.roll(kf, dx, axis=0), dy, axis=1)
        new_kf /= 9.0
        # Blend: 70% diffused + 30% original (preserves hotspots)
        self.knowledge_field = 0.70 * new_kf + 0.30 * kf
        # Slow decay
        self.knowledge_field *= 0.995
        self.knowledge_field = np.clip(self.knowledge_field, 0.0, 10.0)

    def _compute_interference(self):
        """
        When two artifacts of the same category are within radius 8,
        they create constructive interference in the knowledge field.
        Only re-computed every 10 ticks for performance.
        """
        if self.step_count % 10 != 0:
            return

        # Group artifacts by category
        cat_positions: Dict[str, List[Tuple[int, int]]] = {}
        for (x, y), art in self.artifacts.items():
            cat = art.get('type', 'unknown')
            cat_positions.setdefault(cat, []).append((x, y))

        # For each category with 2+ artifacts, create interference
        for cat, positions in cat_positions.items():
            if len(positions) < 2:
                continue
            for i, (x1, y1) in enumerate(positions[:20]):
                for x2, y2 in positions[i+1:20]:
                    dx = min(abs(x1-x2), self.size - abs(x1-x2))
                    dy = min(abs(y1-y2), self.size - abs(y1-y2))
                    dist = np.sqrt(dx*dx + dy*dy)
                    if dist < 8:
                        # Constructive interference at midpoint
                        mx = (x1 + x2) // 2 % self.size
                        my = (y1 + y2) // 2 % self.size
                        boost = 0.15 * np.exp(-dist / 4.0)
                        self.knowledge_field[mx, my] += boost

    def _world_event(self):
        etype = self.rng.choice(
            ['abundance', 'scarcity', 'anomaly', 'plague'],
            p=[0.38, 0.30, 0.22, 0.10]
        )
        cx = self.rng.randint(8, self.size - 8)
        cy = self.rng.randint(8, self.size - 8)
        rad = self.rng.randint(5, 13)

        xs = np.arange(max(0, cx-rad), min(self.size, cx+rad))
        ys = np.arange(max(0, cy-rad), min(self.size, cy+rad))

        if etype == 'abundance':
            for x in xs:
                for y in ys:
                    self.resources[x, y] = np.clip(
                        self.resources[x, y] * 1.9, 0, 8
                    )
            desc = f"🌿 Abundance bloom at ({cx},{cy})"

        elif etype == 'scarcity':
            for x in xs:
                for y in ys:
                    self.resources[x, y] *= 0.25
            desc = f"🌵 Scarcity event at ({cx},{cy})"

        elif etype == 'anomaly':
            r_type = self.rng.randint(0, N_RESOURCES)
            for x in xs:
                for y in ys:
                    self.resources[x, y, r_type] = min(
                        8.0, self.resources[x, y, r_type] + 4.0
                    )
            # Anomalies also boost knowledge field
            for x in xs:
                for y in ys:
                    self.knowledge_field[x, y] += 0.5
            desc = f"🌀 Anomaly ({R_NAMES[r_type]}) at ({cx},{cy})"

        else:  # plague
            for x in xs:
                for y in ys:
                    self.resources[x, y] *= 0.55
            desc = f"☠️ Plague zone at ({cx},{cy})"

        self.resources = np.clip(self.resources, 0.0, 8.0)
        evt = {'step': self.step_count, 'type': etype, 'desc': desc,
               'pos': (cx, cy)}
        self.events.append(evt)
        if len(self.events) > 40:
            self.events.pop(0)

    # ── Resource access ──────────────────────────────────────────────────────

    def consume_resource(self, x: int, y: int, r_type: int,
                         amount: float) -> float:
        x, y     = x % self.size, y % self.size
        available = float(self.resources[x, y, r_type])
        consumed  = min(available, amount)
        self.resources[x, y, r_type] -= consumed
        return consumed

    # ── Knowledge field access ───────────────────────────────────────────────

    def get_knowledge_field(self, x: int, y: int) -> float:
        """Get knowledge field intensity at (x, y)."""
        return float(self.knowledge_field[x % self.size, y % self.size])

    def boost_knowledge_field(self, x: int, y: int,
                              amount: float = 0.5) -> None:
        """Boost knowledge field at (x, y) — called when agents invent."""
        bx, by = x % self.size, y % self.size
        self.knowledge_field[bx, by] = min(
            10.0, self.knowledge_field[bx, by] + amount
        )

    # ── Artifacts ────────────────────────────────────────────────────────────

    def place_artifact(self, x: int, y: int, artifact: dict) -> None:
        x, y = x % self.size, y % self.size
        self.artifacts[(x, y)] = artifact

        # Promote to world knowledge if it's a discoverable concept
        if artifact.get('type') in ('physics', 'math', 'language', 'ideology'):
            self.world_knowledge[artifact['name']] = artifact

        # Store in global memory (autoassociative imprint)
        if 'godel' in artifact:
            psi_enc = self._artifact_to_psi(artifact)
            self.global_memory.store(psi_enc)

    def _artifact_to_psi(self, artifact: dict) -> np.ndarray:
        """Encode an artifact into a K_DIM complex vector for memory storage."""
        godel = artifact.get('godel', 0)
        program = artifact.get('program', ['move'])
        # Use Gödel number as phase seed, program length as amplitude
        psi = np.zeros(K_DIM, dtype=complex)
        for i, prim_name in enumerate(program):
            from metacognition import PRIM_TO_IDX
            idx = PRIM_TO_IDX.get(prim_name, 0)
            phase = 2 * np.pi * idx / 16.0
            dim = (i * 3 + idx) % K_DIM
            psi[dim] += np.exp(1j * phase)
        # Add Gödel-derived harmonics
        for k in range(min(8, K_DIM)):
            psi[k] += np.exp(1j * godel * 0.01 * k) * 0.3
        norm = np.linalg.norm(psi)
        if norm > 1e-12:
            psi /= norm
        return psi

    def get_artifact(self, x: int, y: int) -> Optional[dict]:
        return self.artifacts.get((x % self.size, y % self.size))

    # ── Visualisation helpers ────────────────────────────────────────────────

    def resource_heatmap(self) -> np.ndarray:
        """Sum of all resources per cell."""
        return self.resources.sum(axis=2)

    def knowledge_field_heatmap(self) -> np.ndarray:
        """Knowledge field values for visualisation."""
        return self.knowledge_field.copy()

    def artifact_positions(self) -> Tuple[List[int], List[int]]:
        xs = [k[0] for k in self.artifacts]
        ys = [k[1] for k in self.artifacts]
        return xs, ys

    def get_recent_events(self, n: int = 6) -> List[dict]:
        return self.events[-n:]
