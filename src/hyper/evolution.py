"""
evolution.py — Population Lifecycle Engine v3.0
================================================
Manages the full lifecycle with METACOGNITIVE SELECTION PRESSURE.

NEW in v3.0 (ported from GeNeSIS):
  - Cultural Ratchet Verification: behavioral autocorrelation across generations
  - Behavioral Clustering: KMeans-style eigenvalue archetype assignment
  - DNA Preservation: full simulation state export for replay
  - Adaptive population dynamics with N-tick staggered execution

Invented by Devanik & Claude (Xylia) — Event Horizon Project
"""

import numpy as np
import json
import datetime
from typing import Dict, List, Tuple, Optional

from agents import BioHyperAgent
from world import World
from civilization import CivilizationManager
from metacognition import PhylogeneticTracker, K_META, K_DIM


class EvolutionEngine:
    """
    The outer loop that drives the entire simulation.

    Call initialize() once, then call process_step() every tick.
    All agent births, deaths, world steps, and civilisation updates
    are orchestrated from here.
    """

    INITIAL_POP = 32
    MAX_POP     = 128
    MIN_POP     = 28

    def __init__(self, world_size: int = 60, seed: int = 42):
        self.world_size = world_size
        self.seed       = seed
        self.rng        = np.random.RandomState(seed % (2**31))

        self.agents      : Dict[str, BioHyperAgent] = {}

        # Population bookkeeping
        self.total_born  : int  = 0
        self.total_died  : int  = 0
        self.generation  : int  = 0

        # History for charts
        self.pop_history    : List[int]   = []
        self.energy_history : List[float] = []
        self.inv_history    : List[int]   = []
        self.meta_inv_history : List[int] = []
        self.novelty_history  : List[float] = []

        # Lineage map: agent_id → [child_ids]
        self.lineage : Dict[str, List[str]] = {}

        # Phylogenetic tracker for cognitive clades
        self.phylo = PhylogeneticTracker(threshold=2.5)

        # Meta-fitness ranking (for selection pressure during immigration)
        self._meta_fitness_cache : Dict[str, float] = {}

        # ══════════════════════════════════════════════════════════════════
        # NEW v3.0: Cultural Ratchet — behavioral autocorrelation tracking
        # ══════════════════════════════════════════════════════════════════
        self.gen_behavior_archive : Dict[int, np.ndarray] = {}
        self.tradition_verified   : bool  = False
        self.cultural_continuity  : float = 0.0

        # ══════════════════════════════════════════════════════════════════
        # NEW v3.0: Behavioral Archetypes (KMeans-style clustering)
        # ══════════════════════════════════════════════════════════════════
        self.archetypes        : Dict[str, str] = {}  # agent_id → archetype
        self.archetype_labels  = ['Explorer', 'Builder', 'Fighter', 'Thinker']
        self.archetype_counts  : Dict[str, int] = {}

    # ── Seeding ──────────────────────────────────────────────────────────────

    def initialize(self) -> Dict[str, BioHyperAgent]:
        """
        Spawn 96 initial agents with maximally diverse spectral identities.
        """
        agents = {}
        for i in range(self.INITIAL_POP):
            x = self.rng.randint(2, self.world_size - 2)
            y = self.rng.randint(2, self.world_size - 2)
            a = BioHyperAgent(
                x=x, y=y,
                world_size=self.world_size,
                seed=self.seed + i * 41 + 7,
                generation=0,
            )
            a.energy = self.rng.uniform(7.5, 10.0) # Prevent early death
            agents[a.id] = a
            self.lineage[a.id] = []

        self.agents     = agents
        self.total_born = self.INITIAL_POP
        return agents

    # ── Main tick ────────────────────────────────────────────────────────────

    def process_step(
        self,
        world : World,
        civ   : CivilizationManager,
    ) -> Tuple[Dict[str, BioHyperAgent], List[str]]:
        """
        One simulation tick:
          1. Rebuild spatial index
          2. Step every alive agent
          3. Collect newborns
          4. Remove dead agents
          5. Enforce population floor (meta-fitness weighted immigration)
          6. World physics tick
          7. Civilisation update
          8. Phylogenetic tracking
          9. Record statistics
        """
        events : List[str] = []
        new_children : List[BioHyperAgent] = []

        # Snapshot alive agents for this tick
        alive = {aid: a for aid, a in self.agents.items() if a.alive}
        world.register_agents(list(alive.values()))

        # Step all alive agents
        for agent in list(alive.values()):
            try:
                child = agent.step(world, alive)
            except Exception:
                child = None

            if child is not None:
                new_children.append(child)
                self.lineage.setdefault(agent.id, []).append(child.id)

        # Add newborns (respect ceiling)
        for child in new_children:
            if len(self.agents) < self.MAX_POP:
                self.agents[child.id]  = child
                self.lineage[child.id] = []
                self.total_born       += 1
                self.generation        = max(self.generation, child.generation)
                events.append(
                    f"🐣 Born: {child.id} ← {child.parent_ids[0][:6]}"
                )

        # Remove dead
        dead = [aid for aid, a in self.agents.items() if not a.alive]
        for did in dead:
            age = self.agents[did].age
            events.append(f"💀 Died: {did[:6]} (age {age})")
            del self.agents[did]
            self.total_died += 1

        # Population floor — spawn meta-fitness-weighted immigrants
        n_alive = len(self.agents)
        if n_alive < self.MIN_POP:
            for _ in range(self.MIN_POP - n_alive):
                immigrant = self._spawn_immigrant()
                self.agents[immigrant.id]  = immigrant
                self.lineage[immigrant.id] = []
                self.total_born           += 1
                events.append(f"🌍 Immigrant: {immigrant.id}")

        # World and civilisation tick (pass agents dict for new features)
        world.step(agents=self.agents)
        civ.update(self.agents, world.step_count)

        # Phylogenetic tracking (every 10 ticks for performance)
        if world.step_count % 10 == 0:
            self.phylo.update(self.agents, world.step_count)

            # Check for Cambrian explosions
            recent_novelty = civ.novelty_scorer.novelty_history[-10:]
            pe_event = self.phylo.detect_punctuated_equilibrium(
                recent_novelty, world.step_count
            )
            if pe_event:
                events.append(
                    f"🌋 CAMBRIAN EXPLOSION at tick {world.step_count}! "
                    f"(novelty burst ×{pe_event['ratio']})"
                )

        # Update meta-fitness cache (every 25 ticks)
        if world.step_count % 25 == 0:
            self._update_meta_fitness()

        # Cultural ratchet verification (every 50 ticks)
        if world.step_count % 16 == 0:
            self._check_cultural_ratchet()

        # Behavioral clustering (every 15 ticks)
        if world.step_count % 15 == 0:
            self._behavioral_clustering()

        # Stats bookkeeping
        alive_now = [a for a in self.agents.values() if a.alive]
        self.pop_history.append(len(alive_now))
        if alive_now:
            self.energy_history.append(
                float(np.mean([a.energy for a in alive_now]))
            )
            self.inv_history.append(
                int(sum(len(a.brain.discoveries) for a in alive_now))
            )
            self.meta_inv_history.append(
                int(sum(a.meta.n_meta_inventions for a in alive_now
                        if hasattr(a, 'meta') and a.meta is not None))
            )
            # Average novelty from scorer
            ns = civ.novelty_scorer.get_stats()
            self.novelty_history.append(ns.get('running_mean', 0.0))
        if len(self.pop_history) > 600:
            self.pop_history.pop(0)
            self.energy_history.pop(0)
            self.inv_history.pop(0)
            self.meta_inv_history.pop(0)
            self.novelty_history.pop(0)

        return self.agents, events

    # ── Meta-fitness ─────────────────────────────────────────────────────────

    def _update_meta_fitness(self):
        """
        Compute meta-cognitive fitness for each alive agent:
          fitness = discovery_rate * eigenspread * (1 + meta_inventions)

        This is used to weight who gets cloned during immigration events.
        """
        alive = [a for a in self.agents.values() if a.alive]
        self._meta_fitness_cache = {}
        for a in alive:
            discoveries = len(a.brain.discoveries)
            age = max(1, a.age)
            discovery_rate = discoveries / age * 100.0
            eigenspread = a.meta.eigenspread() if hasattr(a, 'meta') and a.meta else 0.1
            meta_invs = a.meta.n_meta_inventions if hasattr(a, 'meta') and a.meta else 0
            fitness = discovery_rate * eigenspread * (1 + meta_invs * 0.5)
            self._meta_fitness_cache[a.id] = max(0.01, fitness)

    # ══════════════════════════════════════════════════════════════════════════
    # NEW v3.0: CULTURAL RATCHET VERIFICATION
    # ══════════════════════════════════════════════════════════════════════════

    def _check_cultural_ratchet(self):
        """
        Cultural Ratchet: verify that behavioral patterns persist across
        generations without requiring agents to die (Immortality-Safe).
        """
        alive_agents = [a for a in self.agents.values() if a.alive]
        if not alive_agents:
            return

        gen0 = [a for a in alive_agents if a.generation == 0]
        genN = [a for a in alive_agents if a.generation > 0]
        
        if len(gen0) > 4 and len(genN) > 4:
            # Extract the average cognitive mode biases (Culture) of Founders vs Children
            mode_0 = np.mean([[a.action_counts.get(m, 0) for m in ["eat", "trade", "invent", "move_N"]] for a in gen0], axis=0)
            mode_N = np.mean([[a.action_counts.get(m, 0) for m in ["eat", "trade", "invent", "move_N"]] for a in genN], axis=0)
            
            # Prevent zero-variance division errors
            if np.std(mode_0) > 0 and np.std(mode_N) > 0:
                # Calculate Pearson correlation r
                self.cultural_continuity = float(np.corrcoef(mode_0, mode_N)[0, 1])
                # Tradition is verified if correlation is highly positive!
                self.tradition_verified = bool(self.cultural_continuity > 0.55)
            else:
                self.cultural_continuity = 0.0
                self.tradition_verified = False
        else:
            self.cultural_continuity = 0.0
            self.tradition_verified = False

    # ══════════════════════════════════════════════════════════════════════════
    # NEW v3.0: BEHAVIORAL CLUSTERING (KMeans-style archetype assignment)
    # ══════════════════════════════════════════════════════════════════════════

    def _behavioral_clustering(self):
        """
        Cluster agents by eigenvalue fingerprints into 4 archetypes.
        Uses simplified KMeans: assign to nearest centroid.
        """
        alive = [a for a in self.agents.values() if a.alive]
        if len(alive) < 8:
            return

        # Extract eigenvalue fingerprints (first 4 eigenvalues)
        fingerprints = np.array([
            a.brain._evals[:4].real for a in alive
        ])

        # Simple k=4 clustering: use quartiles of first eigenvalue
        sorted_indices = np.argsort(fingerprints[:, 0])
        n = len(alive)
        quarter = max(1, n // 4)

        self.archetypes = {}
        self.archetype_counts = {label: 0 for label in self.archetype_labels}

        for i, agent in enumerate(alive):
            rank = np.searchsorted(sorted_indices, i)
            archetype_idx = min(3, rank // quarter)
            label = self.archetype_labels[archetype_idx]
            self.archetypes[agent.id] = label
            self.archetype_counts[label] = self.archetype_counts.get(label, 0) + 1

    # ══════════════════════════════════════════════════════════════════════════
    # NEW v3.0: DNA PRESERVATION EXPORT
    # ══════════════════════════════════════════════════════════════════════════

    # ══════════════════════════════════════════════════════════════════════════
    # NEW v3.0: 100% UNIVERSE FREEZE & THAW (JSON SAFE)
    # ══════════════════════════════════════════════════════════════════════════

    def freeze_universe(self, civ: CivilizationManager, world: World) -> dict:
        """Captures 100% of the mathematical state for absolute JSON preservation."""
        engine_state = {
            'total_born': self.total_born,
            'total_died': self.total_died,
            'generation': self.generation,
            'pop_history': self.pop_history,
            'energy_history': self.energy_history,
            'inv_history': self.inv_history,
            'meta_inv_history': self.meta_inv_history,
            'novelty_history': self.novelty_history,
            'cultural_continuity': self.cultural_continuity,
            'tradition_verified': self.tradition_verified,
            'archetypes': self.archetypes,
            'archetype_counts': self.archetype_counts,
            'lineage': self.lineage,
            'phylo_clades': {k: list(v) for k, v in self.phylo.clades.items()},
            'phylo_history': self.phylo.clade_history,
            'phylo_cambrian': self.phylo.cambrian_events,
            'gen_behavior_archive': {str(k): v for k, v in self.gen_behavior_archive.items()}
        }

        # Dict keys in JSON must be strings, so we convert tuple coordinates (x,y) to "x,y"
        world_state = {
            'step': world.step_count,
            'resources': world.resources,
            'knowledge_field': world.knowledge_field,
            'pheromone_grid': world.pheromone_grid,
            'meme_grid': world.meme_grid,
            'meme_hue_grid': getattr(world, 'meme_hue_grid', np.zeros((world.size, world.size))),
            'season': world.season,
            'season_timer': world.season_timer,
            'env_phase': world.env_phase,
            'weather_amplitude': world.weather_amplitude,
            'bonds': [list(b) for b in world.bonds],
            'kuramoto_order': world.kuramoto_order_parameter,
            'event_log': getattr(world, '_event_log', []),
            'artifacts': {f"{k[0]},{k[1]}": v for k, v in world.artifacts.items()},
            'cultivator_map': {f"{k[0]},{k[1]}": v for k, v in world.cultivator_map.items()},
            'structures': {
                f"{k[0]},{k[1]}": {'type': v.struct_type, 'builder': v.builder_id, 'age': v.age, 'durability': v.durability, 'created': getattr(v, 'created_tick', 0)}
                for k, v in world.structures.items()
            },
            'mega_resources': {
                f"{k[0]},{k[1]}": {'value': v.value, 'req': v.required_agents}
                for k, v in world.mega_resources.items()
            }
        }

        agent_state = {}
        for aid, a in self.agents.items():
            if not a.alive: continue
            agent_state[aid] = {
                'x': int(a.x), 'y': int(a.y), 'energy': float(a.energy), 'age': int(a.age),
                'health': float(a.health), 'alive': bool(a.alive), 'generation': int(a.generation),
                'parent_ids': getattr(a, 'parent_ids', []),
                'role': getattr(a, 'role', 'Generalist'),
                'inventory': getattr(a, 'inventory', [0,0,0]),
                'trade_count': int(getattr(a, 'trade_count', 0)),
                'punish_count': int(getattr(a, 'punish_count', 0)),
                'kuramoto_phase': float(getattr(a, 'kuramoto_phase', 0.0)),
                'phi_value': float(getattr(a, 'phi_value', 0.0)),
                'social_memory': getattr(a, 'social_memory', {}),
                'causal_model': getattr(a, 'causal_model', {}),
                'internal_phase': float(getattr(a, 'internal_phase', 0.0)),
                'weather_vote': float(getattr(a, 'weather_vote', 0.0)),
                'scratchpad': getattr(a, 'scratchpad', np.zeros((32,32))).tolist(),
                'scratchpad_writes': int(getattr(a, 'scratchpad_writes', 0)),
                'meme_pool': getattr(a, 'meme_pool', []),
                'caste_gene': getattr(a, 'caste_gene', [0,0,0,0]),
                'is_fertile': getattr(a, 'is_fertile', True),
                # ── ADD THE 3 BIOLOGICAL GHOSTS ──
                'strange_loop_active': bool(getattr(a, 'strange_loop_active', False)),
                'last_action': getattr(a, 'last_action', 'rest'),
                'tom_depth': int(getattr(a, 'tom_depth', 0)),
                'tribe_id': getattr(a, 'tribe_id', None),
                'reputation': float(getattr(a, 'reputation', 0.0)),
                'n_kills': int(getattr(a, 'n_kills', 0)),
                'n_children': int(getattr(a, 'n_children', 0)),
                'tools': getattr(a, 'tools', []),
                'absorbed_inventions': getattr(a, 'absorbed_inventions', []),
                'action_counts': getattr(a, 'action_counts', {}),
                'soul_freqs': a.soul_freqs,
                'brain_H': a.brain.H,
                'brain_psi': a.brain.psi,
                'discoveries': a.brain.discoveries,
                'composed_actions': a.brain.composed_actions,
                'emotions': a.brain.emotions,
                'episodic_memory': getattr(a.brain, 'episodic_memory', []),
                'qualia_memories': getattr(a.brain, 'qualia_memories', {}),
                'other_models': getattr(a.brain, 'other_models', {}),
                'prediction_errors': getattr(a.brain, 'prediction_errors', []),
                'n_comms': int(getattr(a.brain, 'n_comms', 0)),
                'total_reward': float(getattr(a.brain, 'total_reward', 0.0)),
                'confidence': float(getattr(a.brain, 'confidence', 1.0)),
                'meta_H': a.meta.meta_H if hasattr(a, 'meta') and a.meta else None,
                'meta_psi': a.meta.meta_psi if hasattr(a, 'meta') and a.meta else None,
                'lr_field': a.meta.lr_field if hasattr(a, 'meta') and a.meta else None,
                'meta_inventions': int(getattr(a.meta, 'n_meta_inventions', 0)) if hasattr(a, 'meta') and a.meta else 0,
            }

        return {
            'timestamp': datetime.datetime.now().isoformat(),
            'version': 'v3.0_immortal',
            'engine': engine_state,
            'rng_state': self.rng.get_state(),
            'world': world_state,
            'agents': agent_state,
            'civ': civ.freeze_civ()
        }

    def thaw_universe(self, state: dict, world: World, civ: CivilizationManager):
        """Restores 100% of the mathematical state from the unzipped JSON dictionary."""
        from world import Trap, Battery, Cultivator, Structure, MegaResource
        
        # 1. Restore Engine
        eng = state['engine']
        self.total_born = eng.get('total_born', 0)
        self.total_died = eng.get('total_died', 0)
        self.generation = eng.get('generation', 0)
        self.pop_history = eng.get('pop_history', [])
        self.energy_history = eng.get('energy_history', [])
        self.inv_history = eng.get('inv_history', [])
        self.meta_inv_history = eng.get('meta_inv_history', [])
        self.novelty_history = eng.get('novelty_history', [])
        self.cultural_continuity = eng.get('cultural_continuity', 0.0)
        self.tradition_verified = eng.get('tradition_verified', False)
        self.archetypes = eng.get('archetypes', {})
        self.archetype_counts = eng.get('archetype_counts', {})
        self.lineage = eng.get('lineage', {})
        self.phylo.clades = {k: set(v) for k, v in eng.get('phylo_clades', {}).items()}
        self.phylo.clade_history = eng.get('phylo_history', [])
        self.phylo.cambrian_events = eng.get('phylo_cambrian', [])
        self.gen_behavior_archive = {int(k): np.array(v) for k, v in eng.get('gen_behavior_archive', {}).items()}

      # ── RESTORE EXACT RNG TIMELINE ──
        if 'rng_state' in state:
            r_list = state['rng_state']
            state_tuple = (r_list[0], np.array(r_list[1], dtype=np.uint32), r_list[2], r_list[3], r_list[4])
            self.rng.set_state(state_tuple)

        # 2. Restore World Matrices
        w_state = state['world']
        world.step_count = w_state['step']
        world.resources = np.array(w_state['resources'])
        world.knowledge_field = np.array(w_state['knowledge_field'])
        world.pheromone_grid = np.array(w_state['pheromone_grid'])
        world.meme_grid = np.array(w_state['meme_grid'])
        world.meme_hue_grid = np.array(w_state.get('meme_hue_grid', np.zeros((world.size, world.size))))
        world.season = w_state.get('season', 0)
        world.season_timer = w_state.get('season_timer', 0)
        world.env_phase = w_state.get('env_phase', 0.0)
        world.weather_amplitude = w_state.get('weather_amplitude', 1.0)
        world.bonds = set(frozenset(b) for b in w_state.get('bonds', []))
        world.kuramoto_order_parameter = w_state.get('kuramoto_order', 0.0)
        world._event_log = w_state.get('event_log', [])

        # Parse string keys "x,y" back to tuple (x,y)
        def parse_pos(k_str):
            p = k_str.split(',')
            return (int(p[0]), int(p[1]))

        world.artifacts = {parse_pos(k): v for k, v in w_state.get('artifacts', {}).items()}
        world.cultivator_map = {parse_pos(k): v for k, v in w_state.get('cultivator_map', {}).items()}
        
        world.structures = {}
        for k_str, s_data in w_state.get('structures', {}).items():
            pos = parse_pos(k_str)
            stype = s_data['type']
            if stype == 'trap':
                s = Trap(pos[0], pos[1], s_data['builder'])
            elif stype == 'battery':
                s = Battery(pos[0], pos[1], s_data['builder'])
            elif stype == 'cultivator':
                s = Cultivator(pos[0], pos[1], s_data['builder'])
            else:
                s = Structure(pos[0], pos[1], stype, s_data['builder'])
            s.age = s_data.get('age', 0)
            s.durability = s_data.get('durability', 100.0)
            s.created_tick = s_data.get('created', 0)
            world.structures[pos] = s

        world.mega_resources = {}
        for k_str, m_data in w_state.get('mega_resources', {}).items():
            pos = parse_pos(k_str)
            world.mega_resources[pos] = MegaResource(pos[0], pos[1], m_data['value'], m_data['req'])

        # 3. Restore Civilization
        civ.thaw_civ(state['civ'])

        # 4. Resurrect Agents
        self.agents = {}
        for aid, adata in state['agents'].items():
            a = BioHyperAgent(x=adata['x'], y=adata['y'], world_size=self.world_size, seed=0)
            a.id = aid
            a.parent_ids = adata.get('parent_ids', [])
            a.energy = adata['energy']
            a.age = adata['age']
            a.health = adata['health']
            a.alive = adata['alive']
            a.generation = adata['generation']
            a.role = adata['role']
            a.inventory = adata['inventory']
            a.trade_count = adata['trade_count']
            a.punish_count = adata['punish_count']
            a.kuramoto_phase = adata['kuramoto_phase']
            a.phi_value = adata['phi_value']
            a.social_memory = adata['social_memory']
            a.causal_model = adata['causal_model']
            a.internal_phase = adata.get('internal_phase', 0.0)
            a.weather_vote = adata.get('weather_vote', 0.0)
            a.scratchpad = np.array(adata.get('scratchpad', np.zeros((32,32))), dtype=np.int8)
            a.scratchpad_writes = adata.get('scratchpad_writes', 0)
            a.meme_pool = adata.get('meme_pool', [])
            a.caste_gene = np.array(adata.get('caste_gene', [0,0,0,0]))
            a.is_fertile = adata.get('is_fertile', True)
            a.strange_loop_active = adata.get('strange_loop_active', False)
            a.last_action = adata.get('last_action', 'rest')
            a.tom_depth = adata.get('tom_depth', 0)
            a.tribe_id = adata.get('tribe_id')
            a.reputation = adata.get('reputation', 0.0)
            a.n_kills = adata.get('n_kills', 0)
            a.n_children = adata.get('n_children', 0)
            a.tools = adata.get('tools', [])
            a.absorbed_inventions = adata.get('absorbed_inventions', [])
            a.action_counts = adata.get('action_counts', {})
            a.soul_freqs = np.array(adata['soul_freqs'])

            # ── Inject the Quantum Brain ──
            a.brain.soul_freqs = a.soul_freqs
            a.brain.H = np.array(adata['brain_H'])
            a.brain.psi = np.array(adata['brain_psi'])
            a.brain.discoveries = adata['discoveries']
            a.brain.composed_actions = adata.get('composed_actions', {})
            a.brain.emotions = np.array(adata['emotions'])
            a.brain.episodic_memory = adata.get('episodic_memory', [])
            a.brain.qualia_memories = {k: np.array(v) for k,v in adata.get('qualia_memories', {}).items()}
            a.brain.other_models = {k: np.array(v) for k,v in adata.get('other_models', {}).items()}
            a.brain.prediction_errors = adata.get('prediction_errors', [])
            a.brain.n_comms = adata.get('n_comms', 0)
            a.brain.total_reward = adata.get('total_reward', 0.0)
            a.brain.confidence = adata.get('confidence', 1.0)

            # ── Inject the Meta Brain ──
            if adata.get('meta_H') is not None:
                a.meta.meta_H = np.array(adata['meta_H'])
                a.meta.meta_psi = np.array(adata['meta_psi'])
                a.meta.lr_field = np.array(adata['lr_field'])
                a.meta.n_meta_inventions = adata['meta_inventions']
                a.meta._recache_meta()

            a.brain._recache()
            self.agents[aid] = a
            
        world.register_agents(list(self.agents.values()))

    # ── Utilities ────────────────────────────────────────────────────────────

    def _spawn_immigrant(self) -> BioHyperAgent:
        """
        Spawn a new agent, potentially inheriting meta-H from the
        most meta-fit living agent (meta-fitness weighted selection).
        """
        side = self.rng.randint(4)
        if   side == 0: x, y = 0, self.rng.randint(0, self.world_size)
        elif side == 1: x, y = self.world_size - 1, self.rng.randint(0, self.world_size)
        elif side == 2: x, y = self.rng.randint(0, self.world_size), 0
        else          : x, y = self.rng.randint(0, self.world_size), self.world_size - 1

        a = BioHyperAgent(
            x=x, y=y, world_size=self.world_size,
            seed=self.rng.randint(0, 2**31),
        )
        a.energy = 8.0

        # Meta-fitness weighted inheritance: copy meta-H from the fittest
        if self._meta_fitness_cache:
            ids     = list(self._meta_fitness_cache.keys())
            weights = np.array([self._meta_fitness_cache[i] for i in ids])
            weights /= weights.sum()
            donor_id = self.rng.choice(ids, p=weights)
            donor    = self.agents.get(donor_id)
            if donor and hasattr(donor, 'meta') and donor.meta is not None:
                # Partial copy with heavy mutation (immigrant = diverse)
                noise = (self.rng.randn(K_META, K_META) + 1j * self.rng.randn(K_META, K_META)) * 0.04
                noise = (noise + noise.conj().T) / 2
                a.meta.meta_H = donor.meta.meta_H * 0.4 + a.meta.meta_H * 0.6 + noise
                a.meta.meta_H = (a.meta.meta_H + a.meta.meta_H.conj().T) / 2
                a.meta._recache_meta()

        return a

    def get_stats(self) -> dict:
        alive = [a for a in self.agents.values() if a.alive]
        n     = len(alive)
        if n == 0:
            return {
                'n_alive': 0, 'total_born': self.total_born,
                'total_died': self.total_died,
                'pop_history': self.pop_history,
            }

        energies    = [a.energy for a in alive]
        ages        = [a.age for a in alive]
        total_inv   = sum(len(a.brain.discoveries) for a in alive)
        total_kills = sum(a.n_kills for a in alive)
        total_kids  = sum(a.n_children for a in alive)
        avg_rep     = float(np.mean([a.reputation for a in alive]))

        # Meta stats
        meta_invs = sum(
            a.meta.n_meta_inventions for a in alive
            if hasattr(a, 'meta') and a.meta is not None
        )
        avg_eigenspread = float(np.mean([
            a.meta.eigenspread() for a in alive
            if hasattr(a, 'meta') and a.meta is not None
        ])) if alive else 0.0
        composed = sum(len(a.brain.composed_actions) for a in alive)

        return {
            'n_alive'         : n,
            'total_born'      : self.total_born,
            'total_died'      : self.total_died,
            'max_generation'  : self.generation,
            'avg_energy'      : round(float(np.mean(energies)), 2),
            'max_energy'      : round(float(np.max(energies)), 2),
            'avg_age'         : round(float(np.mean(ages)), 1),
            'max_age'         : int(np.max(ages)),
            'total_inv'       : total_inv,
            'total_kills'     : total_kills,
            'total_kids'      : total_kids,
            'avg_reputation'  : round(avg_rep, 2),
            'pop_history'     : self.pop_history[-150:],
            'energy_history'  : self.energy_history[-150:],
            'inv_history'     : self.inv_history[-150:],
            # Meta stats
            'total_meta_inv'  : meta_invs,
            'avg_eigenspread' : round(avg_eigenspread, 4),
            'total_composed'  : composed,
            'n_clades'        : len(self.phylo.clades),
            'n_cambrian'      : len(self.phylo.cambrian_events),
            'meta_inv_history': self.meta_inv_history[-150:],
            'novelty_history' : self.novelty_history[-150:],
            # NEW v3.0 stats
            'cultural_continuity': round(self.cultural_continuity, 4),
            'tradition_verified' : self.tradition_verified,
            'archetype_counts'   : self.archetype_counts,
        }

    def top_agents(self, key: str = 'energy', n: int = 10) -> List[dict]:
        alive = [a for a in self.agents.values() if a.alive]
        key_fn = {
            'energy'     : lambda a: a.energy,
            'age'        : lambda a: a.age,
            'inventions' : lambda a: len(a.brain.discoveries),
            'kills'      : lambda a: a.n_kills,
            'children'   : lambda a: a.n_children,
            'reputation' : lambda a: a.reputation,
            'wonder'     : lambda a: float(a.brain.emotions[6]),
            'meta_inv'   : lambda a: (a.meta.n_meta_inventions
                                       if hasattr(a, 'meta') and a.meta else 0),
            'eigenspread': lambda a: (a.meta.eigenspread()
                                       if hasattr(a, 'meta') and a.meta else 0),
        }.get(key, lambda a: a.energy)

        return [a.to_dict() for a in sorted(alive, key=key_fn, reverse=True)[:n]]
