"""
civilization.py — Civilization Dynamics
=========================================
Emergent social structures on top of agent physics.

TRIBE      : Group of resonance-compatible agents (auto-formed by spectral clustering)
DIPLOMACY  : War / alliance emergence from power dynamics (no scripted outcome)
TECH TREE  : Accumulated invention graph — builds naturally from agent discoveries
CULTURE    : Shared knowledge diffusion through wave-coupling communication

No human civilisation is scripted here — everything emerges from:
  - spectral resonance similarity → tribe membership
  - power imbalance → war/alliance decisions
  - invention propagation → technology accumulation
  - artifact placement + absorption → cultural diffusion

Invented by Devanik & Claude (Xylia) — Event Horizon Project
"""

import numpy as np
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field


# ════════════════════════════════════════════════════════════════════════════
@dataclass
class Tribe:
    """A social group sharing spectral resonance."""
    id        : str
    founder   : str
    members   : Set[str]       = field(default_factory=set)
    wars      : Set[str]       = field(default_factory=set)   # tribe IDs at war
    alliances : Set[str]       = field(default_factory=set)   # tribe IDs allied
    knowledge : List[str]      = field(default_factory=list)  # shared discoveries
    power     : float          = 1.0
    n_disc    : int            = 0
    color     : Optional[str]  = None
    founded_step : int         = 0


# ════════════════════════════════════════════════════════════════════════════
class TechTree:
    """
    Civilization's accumulated technology graph.
    Nodes = individual inventions (physics / tool / language / math / ideology)
    Edges = nearest-signature parent (automatic topology)
    Global bonus = multiplicative effect on all agent capabilities (small, accumulative)
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

    def add(self, invention: dict, agent_id: str, tribe_id: Optional[str]) -> bool:
        """Register invention. Returns True if novel (not already known)."""
        name = invention.get('name', '')
        if not name or name in self.nodes:
            return False

        self.nodes[name] = {
            **invention,
            'discoverer'  : agent_id,
            'tribe'       : tribe_id,
        }

        # Connect to nearest existing node by signature distance
        if len(self.nodes) > 1:
            sig     = invention.get('signature', 0)
            best    = min(
                (n for n in self.nodes if n != name),
                key=lambda n: abs(self.nodes[n].get('signature', 0) - sig),
                default=None
            )
            if best:
                self.edges.append((best, name))

        # Small cumulative tech bonus per discovery
        self.global_bonus = min(3.0, self.global_bonus * 1.003)
        return True

    def summary_by_category(self) -> Dict[str, int]:
        counts : Dict[str, int] = {}
        for node in self.nodes.values():
            cat = node.get('type', 'unknown')
            counts[cat] = counts.get(cat, 0) + 1
        return counts

    def recent(self, n: int = 8) -> List[dict]:
        return list(self.nodes.values())[-n:]


# ════════════════════════════════════════════════════════════════════════════
class CivilizationManager:
    """
    Orchestrates tribal dynamics on top of agent physics.

    Each tick:
      1. Tribe assignment (spectral resonance clustering)
      2. Diplomacy (war / alliance every 25 ticks)
      3. Tech tree harvest (collect new inventions)
      4. Tribe power recalculation

    All outcomes are emergent — no scripted civilisation trajectory.
    """

    MAX_TRIBE_SIZE = 28

    def __init__(self, world_size: int = 60):
        self.tribes      : Dict[str, Tribe] = {}
        self.tech        = TechTree()
        self.world_size  = world_size
        self.rng         = np.random.RandomState(777)
        self.step        = 0

        # Global counters
        self.total_wars       = 0
        self.total_alliances  = 0
        self.total_inventions = 0
        self.extinctions      = 0

        # Civilisation event log
        self.civ_events : List[dict] = []

    # ── Main update ──────────────────────────────────────────────────────────

    def update(self, agents: Dict, world_step: int) -> None:
        self.step  = world_step
        alive      = {aid: a for aid, a in agents.items() if a.alive}
        if not alive:
            return

        self._update_tribes(alive)

        if world_step % 25 == 0 and len(self.tribes) >= 2:
            self._diplomacy()

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
        best_id      = None
        best_coup    = 0.32       # minimum resonance threshold

        for tid, tribe in self.tribes.items():
            if len(tribe.members) >= self.MAX_TRIBE_SIZE:
                continue
            sample = [all_agents[i] for i, a in enumerate(all_agents)
                      if a.id in tribe.members][:6]
            if not sample:
                continue
            avg = float(np.mean([agent.brain.resonate(s.brain) for s in sample]))
            if avg > best_coup:
                best_coup = avg
                best_id   = tid

        if best_id:
            agent.tribe_id = best_id
            self.tribes[best_id].members.add(agent.id)
        else:
            tid          = f"T{len(self.tribes)+1:03d}"
            rgb          = agent.brain.spectral_rgb()
            tribe        = Tribe(
                id=tid, founder=agent.id,
                members={agent.id},
                color=f'rgb({rgb[0]},{rgb[1]},{rgb[2]})',
                founded_step=self.step,
            )
            self.tribes[tid]  = tribe
            agent.tribe_id    = tid
            self._log('new_tribe', f"🌱 Tribe {tid} founded by {agent.id}")

    def _dissolve(self, tid: str) -> None:
        if tid in self.tribes:
            del self.tribes[tid]
            self.extinctions += 1
            self._log('extinction', f"💀 Tribe {tid} went extinct")

    # ── Diplomacy ────────────────────────────────────────────────────────────

    def _diplomacy(self) -> None:
        tlist = list(self.tribes.values())
        for i, a in enumerate(tlist):
            for b in tlist[i+1:]:
                if b.id in a.wars or b.id in a.alliances:
                    continue
                ratio = a.power / (b.power + 1e-3)

                # Stronger attacks weaker (> 1.6x power gap)
                if ratio > 1.6 and self.rng.random() < 0.10:
                    self._war(a, b)
                elif ratio < 0.625 and self.rng.random() < 0.10:
                    self._war(b, a)
                # Similar powers → alliance
                elif 0.65 < ratio < 1.54 and self.rng.random() < 0.11:
                    self._ally(a, b)

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
                    cat = inv.get('type', '?')
                    icon = TechTree.CATEGORY_META.get(cat, {}).get('icon', '?')
                    self._log('invention',
                              f"{icon} {agent.id} ({agent.tribe_id or '?'}) → {name}")

    # ── Power ────────────────────────────────────────────────────────────────

    def _recalc_power(self, alive: Dict) -> None:
        for tribe in self.tribes.values():
            members = [alive[aid] for aid in tribe.members if aid in alive]
            if members:
                tribe.power = (
                    sum(a.energy for a in members) * 0.35 +
                    sum(a.health for a in members) * 0.25 +
                    tribe.n_disc * 2.5 +
                    len(tribe.members) * 0.60 +
                    len(tribe.alliances) * 1.5
                )

    # ── Logging ──────────────────────────────────────────────────────────────

    def _log(self, etype: str, desc: str) -> None:
        self.civ_events.append({'step': self.step, 'type': etype, 'desc': desc})
        if len(self.civ_events) > 60:
            self.civ_events.pop(0)

    # ── Stats / queries ──────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        active_wars      = sum(len(t.wars) for t in self.tribes.values()) // 2
        active_alliances = sum(len(t.alliances) for t in self.tribes.values()) // 2
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
        }

    def get_recent_events(self, n: int = 12) -> List[dict]:
        return self.civ_events[-n:]

    def tribe_leaderboard(self) -> List[dict]:
        rows = []
        for tid, tribe in sorted(self.tribes.items(), key=lambda x: -x[1].power):
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
