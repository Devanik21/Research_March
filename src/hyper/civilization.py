"""
civilization.py — Civilization Dynamics v2.0
==============================================
Emergent social structures with METACOGNITIVE epistemics.

TRIBE      : Group of resonance-compatible agents (auto-formed by spectral clustering)
DIPLOMACY  : War / alliance emergence from power + epistemic compatibility
TECH TREE  : Accumulated invention graph — Gödel-encoded behavioral programs
CULTURE    : Shared knowledge diffusion through wave-coupling communication
EPISTEMICS : Tribal meta-H (shared learning paradigm), epistemic schisms

New features:
  - Tribal CivilizationMemory (per-tribe knowledge paradigm)
  - Tribal meta-H (averaged meta-Hamiltonians of members)
  - NoveltyScorer for breakthrough detection
  - Epistemic schisms (alliance breaks when worldviews diverge)

All outcomes are emergent — no scripted civilisation trajectory.

Invented by Devanik & Claude (Xylia) — Event Horizon Project
"""

import numpy as np
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field

from metacognition import (
    K_DIM, K_META,
    CivilizationMemory, NoveltyScorer, GODEL,
)


# ════════════════════════════════════════════════════════════════════════════
@dataclass
class Tribe:
    """A social group sharing spectral resonance and epistemic identity."""
    id            : str
    founder       : str
    members       : Set[str]       = field(default_factory=set)
    wars          : Set[str]       = field(default_factory=set)
    alliances     : Set[str]       = field(default_factory=set)
    knowledge     : List[str]      = field(default_factory=list)
    power         : float          = 1.0
    n_disc        : int            = 0
    color         : Optional[str]  = None
    founded_step  : int            = 0

    # ── New metacognitive fields ─────────────────────────────────────────
    tribal_meta_H : Optional[np.ndarray] = None      # averaged meta-H
    tribal_memory : Optional[CivilizationMemory] = None  # per-tribe memory


# ════════════════════════════════════════════════════════════════════════════
class TechTree:
    """
    Civilization's accumulated technology graph.
    Nodes = individual inventions (Gödel-encoded behavioral programs)
    Edges = nearest-signature parent (automatic topology)
    Global bonus = multiplicative effect on all agent capabilities
    """

    CATEGORY_META = {
        'physics'  : {'icon': '⚛',  'color': '#7DF9FF'},
        'tool'     : {'icon': '🔧',  'color': '#FFD700'},
        'language' : {'icon': '📜',  'color': '#98FB98'},
        'math'     : {'icon': '∑',   'color': '#DDA0DD'},
        'ideology' : {'icon': '🧠',  'color': '#FF8C00'},
        'legacy'   : {'icon': '👻',  'color': '#888888'},
    }

    def __init__(self):
        self.nodes        : Dict[str, dict] = {}
        self.edges        : List[Tuple[str,str]] = []
        self.global_bonus : float = 1.0

    def add(self, invention: dict, agent_id: str,
            tribe_id: Optional[str]) -> bool:
        """Register invention. Returns True if novel."""
        name = invention.get('name', '')
        if not name or name in self.nodes:
            return False

        self.nodes[name] = {
            **invention,
            'discoverer': agent_id,
            'tribe': tribe_id,
        }

        # Connect to nearest existing node by Gödel distance
        if len(self.nodes) > 1:
            sig  = invention.get('signature', 0)
            best = min(
                (n for n in self.nodes if n != name),
                key=lambda n: abs(self.nodes[n].get('signature', 0) - sig),
                default=None
            )
            if best:
                self.edges.append((best, name))

        # Cumulative tech bonus
        self.global_bonus = min(3.0, self.global_bonus * 1.003)
        return True

    def summary_by_category(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for node in self.nodes.values():
            cat = node.get('type', 'unknown')
            counts[cat] = counts.get(cat, 0) + 1
        return counts

    def recent(self, n: int = 8) -> List[dict]:
        return list(self.nodes.values())[-n:]


# ════════════════════════════════════════════════════════════════════════════
class CivilizationManager:
    """
    Orchestrates tribal dynamics with metacognitive epistemics.

    Each tick:
      1. Tribe assignment (spectral resonance clustering)
      2. Tribal meta-H update (average of member meta-Hamiltonians)
      3. Diplomacy (war / alliance / epistemic schisms)
      4. Tech tree harvest (with novelty scoring)
      5. Tribe power recalculation
    """

    MAX_TRIBE_SIZE   = 64
    SCHISM_THRESHOLD = 48.0   # epistemic divergence threshold

    def __init__(self, world_size: int = 60):
        self.tribes      : Dict[str, Tribe] = {}
        self.tech        = TechTree()
        self.world_size  = world_size
        self.rng         = np.random.RandomState(777)
        self.step        = 0

        # NoveltyScorer for breakthrough detection
        self.novelty_scorer = NoveltyScorer()

        # Global counters
        self.total_wars       = 0
        self.total_alliances  = 0
        self.total_inventions = 0
        self.extinctions      = 0
        self.total_schisms    = 0

        # NEW v3.0: Trade tracking
        self.total_trades     = 0

        # Civilisation event log
        self.civ_events : List[dict] = []

    # ── Main update ──────────────────────────────────────────────────────────

    def update(self, agents: Dict, world_step: int) -> None:
        self.step  = world_step
        alive      = {aid: a for aid, a in agents.items() if a.alive}
        if not alive:
            return

        self._update_tribes(alive)
        self._update_tribal_meta_H(alive)

        if world_step % 10 == 0 and len(self.tribes) >= 2:
            self._diplomacy(alive)

        self._harvest_inventions(alive)
        self._recalc_power(alive)

    # ── Tribe management ─────────────────────────────────────────────────────

    def _update_tribes(self, alive: Dict) -> None:
        alive_ids = set(alive.keys())

        # Clean dead members
        empty = []
        for tid, tribe in self.tribes.items():
            tribe.members &= alive_ids
            if not tribe.members:
                empty.append(tid)
        for tid in empty:
            self._dissolve(tid)

        # Assign unaffiliated agents
        for agent in alive.values():
            if agent.tribe_id is None or agent.tribe_id not in self.tribes:
                self._assign(agent, list(alive.values()))

    def _assign(self, agent, all_agents: list) -> None:
        """Find best-fit tribe or create new one."""
        best_id   = None
        best_coup = 0.08

      # ── THE LIQUID DUNBAR'S NUMBER (Societal Singularity) ──
        # A true intelligence has no hardcoded social boundaries.
        # Social capacity scales dynamically with the civilization's Tech Tree.
        # Starts at 12 (forces early diversity, triggering alliances).
        # Every new invention expands their capacity by 3. 
        # At 100 inventions, a single tribe can hold 312 agents (Planetary Scale!)
        liquid_max_size = 12 + (len(self.tech.nodes) * 3)

        for tid, tribe in self.tribes.items():
            # Use the liquid boundary instead of the static MAX_TRIBE_SIZE
            if len(tribe.members) >= liquid_max_size:
                continue
                
            sample = [a for a in all_agents if a.id in tribe.members][:6]
            if not sample:
                continue
            avg = float(np.mean([
                agent.brain.resonate(s.brain) for s in sample
            ]))
            if avg > best_coup:
                best_coup = avg
                best_id   = tid


        if best_id:
            agent.tribe_id = best_id
            self.tribes[best_id].members.add(agent.id)
        else:
            tid   = f"T{len(self.tribes)+1:03d}"
            rgb   = agent.brain.spectral_rgb()
            tribe = Tribe(
                id=tid, founder=agent.id,
                members={agent.id},
                color=f'rgb({rgb[0]},{rgb[1]},{rgb[2]})',
                founded_step=self.step,
                tribal_memory=CivilizationMemory(dim=K_DIM, eta=0.06),
            )
            self.tribes[tid] = tribe
            agent.tribe_id   = tid
            self._log('new_tribe',
                       f"🌱 Tribe {tid} founded by {agent.id}")

    def _dissolve(self, tid: str) -> None:
        if tid in self.tribes:
            del self.tribes[tid]
            self.extinctions += 1
            self._log('extinction', f"💀 Tribe {tid} went extinct")

    # ── Tribal Meta-H update ─────────────────────────────────────────────────

    def _update_tribal_meta_H(self, alive: Dict) -> None:
        """
        Compute each tribe's shared epistemic identity:
        tribal_meta_H = average of member meta-Hamiltonians.

        Members' meta_H is partially shifted toward the tribal average
        (cultural assimilation, 5% per tick).
        """
        for tribe in self.tribes.values():
            members = [alive[aid] for aid in tribe.members if aid in alive]
            if not members:
                continue

            # Compute average meta-H across tribe
            meta_Hs = []
            for m in members:
                if hasattr(m, 'meta') and m.meta is not None:
                    meta_Hs.append(m.meta.meta_H)

            if not meta_Hs:
                continue

            avg_meta_H = np.mean(meta_Hs, axis=0)
            avg_meta_H = (avg_meta_H + avg_meta_H.conj().T) / 2
            tribe.tribal_meta_H = avg_meta_H

            # Cultural assimilation: nudge each member toward tribal average
            for m in members:
                if hasattr(m, 'meta') and m.meta is not None:
                    assim_rate = 0.05
                    m.meta.meta_H = ((1 - assim_rate) * m.meta.meta_H
                                     + assim_rate * avg_meta_H)
                    m.meta.meta_H = (m.meta.meta_H
                                     + m.meta.meta_H.conj().T) / 2
                    m.meta._recache_meta()

    # ── Diplomacy ────────────────────────────────────────────────────────────

    def _diplomacy(self, alive: Dict) -> None:
        tlist = list(self.tribes.values())
        for i, a in enumerate(tlist):
            for b in tlist[i+1:]:
                if b.id in a.wars or b.id in a.alliances:
                    # Check for epistemic schism in existing alliances
                    if b.id in a.alliances:
                        self._check_schism(a, b)
                    continue

                ratio = a.power / (b.power + 1e-3)

                if 0.5 < ratio < 2.0 and self.rng.random() < 0.60:
                    self._ally(a, b)
                elif (ratio > 3.0 or ratio < 0.33) and self.rng.random() < 0.02:
                    # War ONLY happens under extreme power disparity AND rarity
                    self._war(a, b)
                  

    def _war(self, aggressor: Tribe, target: Tribe) -> None:
        aggressor.wars.add(target.id)
        target.wars.add(aggressor.id)
        aggressor.alliances.discard(target.id)
        target.alliances.discard(aggressor.id)
        self.total_wars += 1
        self._log('war', f"⚔️  WAR: {aggressor.id} → {target.id}")

    def _ally(self, a: Tribe, b: Tribe) -> None:
        a.alliances.add(b.id)
        b.alliances.add(a.id)
        a.wars.discard(b.id)
        b.wars.discard(a.id)
        self.total_alliances += 1
        self._log('alliance', f"🤝 ALLIANCE: {a.id} + {b.id}")

    def _check_schism(self, a: Tribe, b: Tribe) -> None:
        """
        Epistemic schism: when two allied tribes' meta-Hamiltonians
        diverge beyond threshold, the alliance breaks.
        """
        if a.tribal_meta_H is None or b.tribal_meta_H is None:
            return

        # Spectral distance between tribal meta-Hamiltonians
        evals_a = np.linalg.eigvalsh(a.tribal_meta_H)
        evals_b = np.linalg.eigvalsh(b.tribal_meta_H)
        dist = float(np.linalg.norm(evals_a - evals_b))

        if dist > self.SCHISM_THRESHOLD:
            a.alliances.discard(b.id)
            b.alliances.discard(a.id)
            self.total_schisms += 1
            self._log('schism',
                       f"🔱 SCHISM: {a.id} ↔ {b.id} "
                       f"(epistemic distance: {dist:.2f})")

    # ── Technology ───────────────────────────────────────────────────────────

    def _harvest_inventions(self, alive: Dict) -> None:
        for agent in alive.values():
            for name, inv in agent.brain.discoveries.items():
                if self.tech.add(inv, agent.id, agent.tribe_id):
                    self.total_inventions += 1
                    tribe = self.tribes.get(agent.tribe_id)
                    if tribe:
                        tribe.n_disc += 1
                        if name not in tribe.knowledge:
                            tribe.knowledge.append(name)

                        # Store in tribal memory
                        if tribe.tribal_memory is not None:
                            psi_enc = self._invention_to_psi(inv)
                            tribe.tribal_memory.store(psi_enc)

                    # Score novelty
                    godel = inv.get('godel', 0)
                    program = inv.get('program', ['move'])
                    psi_enc = self._invention_to_psi(inv)

                    from world import World
                    # We need the global memory from the world to score
                    # but we receive it indirectly; use a dummy if needed
                    dummy_mem = CivilizationMemory(dim=K_DIM)
                    if tribe and tribe.tribal_memory:
                        dummy_mem = tribe.tribal_memory

                    novelty, is_breakthrough = self.novelty_scorer.score(
                        godel, program, dummy_mem, psi_enc
                    )

                    cat  = inv.get('type', '?')
                    icon = TechTree.CATEGORY_META.get(cat, {}).get('icon', '?')
                    desc = (f"{icon} {agent.id} ({agent.tribe_id or '?'}) "
                            f"→ {name}")

                    if is_breakthrough:
                        desc = f"🌟 BREAKTHROUGH! {desc} (novelty: {novelty:.3f})"
                        self._log('breakthrough', desc)
                    else:
                        self._log('invention', desc)

    def _invention_to_psi(self, inv: dict) -> np.ndarray:
        """Encode invention into K_DIM complex vector."""
        from metacognition import PRIM_TO_IDX
        godel = inv.get('godel', 0)
        program = inv.get('program', ['move'])
        psi = np.zeros(K_DIM, dtype=complex)
        for i, prim_name in enumerate(program):
            idx = PRIM_TO_IDX.get(prim_name, 0)
            phase = 2 * np.pi * idx / 16.0
            dim = (i * 3 + idx) % K_DIM
            psi[dim] += np.exp(1j * phase)
        for k in range(min(8, K_DIM)):
            psi[k] += np.exp(1j * godel * 0.01 * k) * 0.3
        norm = np.linalg.norm(psi)
        if norm > 1e-12:
            psi /= norm
        return psi

    # ── Power ────────────────────────────────────────────────────────────────

    def _recalc_power(self, alive: Dict) -> None:
        for tribe in self.tribes.values():
            members = [alive[aid] for aid in tribe.members if aid in alive]
            if members:
                # Include meta-cognitive diversity as power component
                meta_spreads = [
                    m.meta.eigenspread() for m in members
                    if hasattr(m, 'meta') and m.meta is not None
                ]
                avg_meta = np.mean(meta_spreads) if meta_spreads else 0.0

                # Include phi (integrated information) in power
                phi_values = [
                    getattr(m, 'phi_value', 0.0) for m in members
                ]
                avg_phi = np.mean(phi_values) if phi_values else 0.0

                # Include trade activity in power
                total_trades = sum(
                    getattr(m, 'trade_count', 0) for m in members
                )
                self.total_trades += total_trades

                tribe.power = (
                    sum(a.energy for a in members) * 0.30 +
                    sum(a.health for a in members) * 0.20 +
                    tribe.n_disc * 2.5 +
                    len(tribe.members) * 0.55 +
                    len(tribe.alliances) * 1.5 +
                    avg_meta * 3.0 +     # meta-cognitive diversity bonus
                    avg_phi * 5.0 +      # consciousness bonus
                    total_trades * 0.1   # economic activity bonus
                )

    # ── Logging ──────────────────────────────────────────────────────────────

    def _log(self, etype: str, desc: str) -> None:
        self.civ_events.append({
            'step': self.step, 'type': etype, 'desc': desc
        })
        if len(self.civ_events) > 80:
            self.civ_events.pop(0)

    # ── Stats / queries ──────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        active_wars = sum(len(t.wars) for t in self.tribes.values()) // 2
        active_alliances = sum(
            len(t.alliances) for t in self.tribes.values()
        ) // 2
        return {
            'n_tribes'         : len(self.tribes),
            'active_wars'      : active_wars,
            'active_alliances' : active_alliances,
            'total_wars'       : self.total_wars,
            'total_alliances'  : self.total_alliances,
            'total_inventions' : self.total_inventions,
            'tech_bonus'       : round(self.tech.global_bonus, 4),
            'world_knowledge'  : len(self.tech.nodes),
            'extinctions'      : self.extinctions,
            'total_schisms'    : self.total_schisms,
            'n_breakthroughs'  : len(self.novelty_scorer.breakthroughs),
            # NEW v3.0
            'total_trades'     : self.total_trades,
        }

    def get_recent_events(self, n: int = 12) -> List[dict]:
        return self.civ_events[-n:]

    def tribe_leaderboard(self) -> List[dict]:
        rows = []
        for tid, tribe in sorted(
            self.tribes.items(), key=lambda x: -x[1].power
        ):
            rows.append({
                'id'       : tid,
                'members'  : len(tribe.members),
                'power'    : round(tribe.power, 1),
                'disc'     : tribe.n_disc,
                'wars'     : len(tribe.wars),
                'allies'   : len(tribe.alliances),
                'color'    : tribe.color or '#7DF9FF',
            })
        return rows
