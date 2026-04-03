"""
metacognition.py — Self-Referential Meta-Cognitive Engine
==========================================================
The mathematical foundation for HyperAgent self-improvement.

Inspired by Meta FAIR HyperAgents (arXiv:2603.19461):
  Task agent + meta agent = SAME editable program.

Modules:
  MetaConsciousness   — dual-band Hamiltonian (task + meta) with self-modifying learn rules
  GodelEncoder        — encodes/decodes primitive action sequences as unique integers
  CivilizationMemory  — sparse autoassociative matrix for collective knowledge retrieval
  NoveltyScorer       — measures discovery novelty and detects Breakthroughs
  PhylogeneticTracker — tracks cognitive clades and meta-learner lineage trees

All math is pure NumPy. No LLMs. No external models. Emergent everything.

Invented by Devanik & Claude (Xylia) — Event Horizon Project
"""

import numpy as np
from typing import Optional, Dict, List, Tuple, Set

# ── Global constants (shared across all modules) ─────────────────────────────
K_DIM       = 32        # Total Hilbert space dimension per agent
K_TASK      = 16        # Dims 0–15: task-level cognition
K_META      = 16        # Dims 16–31: meta-cognition (learning about learning)
META_DT     = 0.04      # Meta-level Schrödinger time step (slower than task)
GODEL_BASE  = 17        # Base for Gödel encoding (prime, > number of primitives)
MAX_PROGRAM_LEN = 8     # Maximum length of a behavioral program


# ══════════════════════════════════════════════════════════════════════════════
# PRIMITIVE ACTION ALGEBRA
# ══════════════════════════════════════════════════════════════════════════════

PRIMITIVES = {
    'spatial':    ['move', 'jump', 'spiral', 'retreat'],
    'metabolic':  ['eat', 'fast', 'store', 'burn'],
    'social':     ['signal', 'mimic', 'teach', 'isolate'],
    'cognitive':  ['reflect', 'dream', 'focus', 'diffuse'],
}

# Flat list of all primitives (order matters for Gödel encoding)
ALL_PRIMITIVES = []
for category in ['spatial', 'metabolic', 'social', 'cognitive']:
    ALL_PRIMITIVES.extend(PRIMITIVES[category])

N_PRIMITIVES   = len(ALL_PRIMITIVES)   # 16 primitives
PRIM_TO_IDX    = {p: i for i, p in enumerate(ALL_PRIMITIVES)}
IDX_TO_PRIM    = {i: p for i, p in enumerate(ALL_PRIMITIVES)}

# Category lookup for each primitive
PRIM_CATEGORY  = {}
for cat, prims in PRIMITIVES.items():
    for p in prims:
        PRIM_CATEGORY[p] = cat


# ══════════════════════════════════════════════════════════════════════════════
# GÖDEL ENCODER — Programs as Numbers
# ══════════════════════════════════════════════════════════════════════════════

class GodelEncoder:
    """
    Encodes and decodes behavioral programs (sequences of primitives) as
    unique integers using a base-17 positional encoding.

    A "program" is a sequence of 2–8 primitive action indices.
    The Gödel number is:  G = Σ (prim_idx[i] + 1) * BASE^i

    Two programs with similar Gödel numbers have similar prefix structure —
    enabling spectral distance to measure "conceptual distance" between
    inventions.
    """

    def __init__(self):
        self.base = GODEL_BASE

    def encode(self, program: List[str]) -> int:
        """Encode a list of primitive names to a Gödel number."""
        g = 0
        for i, prim in enumerate(program[:MAX_PROGRAM_LEN]):
            idx = PRIM_TO_IDX.get(prim, 0)
            g += (idx + 1) * (self.base ** i)
        return g

    def decode(self, godel: int) -> List[str]:
        """Decode a Gödel number back to a list of primitive names."""
        program = []
        n = abs(int(godel))
        while n > 0 and len(program) < MAX_PROGRAM_LEN:
            remainder = n % self.base
            if remainder == 0:
                remainder = self.base
            idx = remainder - 1
            idx = max(0, min(idx, N_PRIMITIVES - 1))
            program.append(IDX_TO_PRIM[idx])
            n = (n - remainder) // self.base
        return program if program else ['move']

    def distance(self, g1: int, g2: int) -> float:
        """Spectral distance between two Gödel numbers (log-scale)."""
        return abs(np.log1p(abs(g1)) - np.log1p(abs(g2)))

    def diversity_score(self, program: List[str]) -> float:
        """How many distinct categories does this program span? [0, 1]."""
        cats = set(PRIM_CATEGORY.get(p, 'unknown') for p in program)
        return len(cats) / 4.0   # 4 categories max

    def random_program(self, rng: np.random.RandomState, length: int = None
                       ) -> List[str]:
        """Generate a random behavioral program."""
        if length is None:
            length = rng.randint(2, MAX_PROGRAM_LEN + 1)
        return [ALL_PRIMITIVES[rng.randint(N_PRIMITIVES)] for _ in range(length)]


# Global encoder singleton
GODEL = GodelEncoder()


# ══════════════════════════════════════════════════════════════════════════════
# META-CONSCIOUSNESS — The Self-Modifying Mind
# ══════════════════════════════════════════════════════════════════════════════

class MetaConsciousness:
    """
    The meta-cognitive layer that sits alongside the task-level HRC brain.

    meta_H   : K_META × K_META Hermitian matrix — models the learning process
    meta_psi : K_META complex vector — current meta-cognitive state
    lr_field : K_META real vector — per-dimension learning rates (evolvable)

    The meta layer controls HOW the task layer learns:
      1. meta_psi evolves under meta_H (Schrödinger, same as task level)
      2. The magnitude profile of meta_psi modulates per-dimension learning rates
      3. Meta-inventions = perturbations to meta_H itself (learning new learning)
    """

    def __init__(self, soul_freqs: np.ndarray, seed: int = 0):
        self.K     = K_META
        self.rng   = np.random.RandomState(seed % (2**31))

        # ── Meta wave function ────────────────────────────────────────────
        raw           = self.rng.randn(K_META) + 1j * self.rng.randn(K_META)
        self.meta_psi = raw / (np.linalg.norm(raw) + 1e-12)

        # ── Meta Hamiltonian ──────────────────────────────────────────────
        self.meta_H = self._init_meta_H(soul_freqs)
        self._meta_evals, self._meta_evecs = np.linalg.eigh(self.meta_H)

        # ── Per-dimension learning rate field ─────────────────────────────
        self.lr_field = np.full(K_META, 0.007, dtype=float)

        # ── Counters ──────────────────────────────────────────────────────
        self.n_meta_inventions = 0
        self.cognitive_surprise_history: List[float] = []

    def _init_meta_H(self, soul_freqs: np.ndarray) -> np.ndarray:
        """Initialize meta-Hamiltonian from soul frequency harmonics."""
        # Use higher harmonics of soul for meta-level identity
        meta_freqs = np.zeros(K_META, dtype=float)
        n = min(len(soul_freqs), K_META)
        meta_freqs[:n] = soul_freqs[:n] * 0.3 + 0.5
        H = np.diag(meta_freqs.astype(complex))
        off = (self.rng.randn(K_META, K_META)
               + 1j * self.rng.randn(K_META, K_META)) * 0.08
        H += (off + off.conj().T) / 2
        return (H + H.conj().T) / 2

    def _recache_meta(self):
        self._meta_evals, self._meta_evecs = np.linalg.eigh(self.meta_H)

    # ── Meta evolution ────────────────────────────────────────────────────

    def evolve_meta(self, dt: float = META_DT) -> None:
        """Schrödinger step on the meta wave function."""
        phase          = np.exp(-1j * self._meta_evals * dt)
        Vdagpsi        = self._meta_evecs.conj().T @ self.meta_psi
        self.meta_psi  = self._meta_evecs @ (phase * Vdagpsi)
        norm           = np.linalg.norm(self.meta_psi)
        if norm > 1e-12:
            self.meta_psi /= norm

    # ── Meta-modulated learning ───────────────────────────────────────────

    def compute_lr_modulation(self) -> np.ndarray:
        """
        Use meta_psi magnitude profile to modulate per-dimension learning rates.
        Returns a K_META vector of learning rate multipliers in [0.2, 3.0].
        """
        magnitudes = np.abs(self.meta_psi)
        magnitudes = magnitudes / (magnitudes.max() + 1e-12)
        modulation = 0.2 + 2.8 * magnitudes
        return modulation

    def compute_meta_dH(self, reward: float, task_psi: np.ndarray
                        ) -> np.ndarray:
        """
        The meta layer computes the actual gradient update for the task-level H.

        Instead of the fixed rule:  dH = sign * lr * outer(ψ, ψ†)
        The meta layer generates:   dH = meta_modulated_lr * rotated_outer

        The rotation is determined by meta_psi — effectively, the meta layer
        chooses WHICH directions in Hilbert space to reinforce.
        """
        K = len(task_psi)
        sign = 1.0 if reward >= 0 else -1.0
        lr   = min(abs(reward), 3.0)

        # Meta-modulated learning rates (broadcast to task dimensions)
        modulation = self.compute_lr_modulation()
        # Extend modulation to full K_DIM if task_psi is larger than K_META
        full_mod = np.ones(K, dtype=float)
        full_mod[:K_META] = modulation

        # Outer product of task psi, weighted by meta modulation
        outer = np.outer(task_psi, task_psi.conj())
        # Apply per-dimension modulation as diagonal scaling
        scale = np.sqrt(np.outer(full_mod, full_mod))
        dH    = sign * lr * 0.007 * outer * scale
        dH    = (dH + dH.conj().T) / 2
        return dH

    # ── Meta-invention ────────────────────────────────────────────────────

    def attempt_meta_invention(self, wonder: float, curiosity: float,
                               age: int) -> Optional[dict]:
        """
        Attempt to mutate the agent's own learning algorithm (meta_H).

        Gated by: wonder > 0.7 AND curiosity > 0.6 AND age > 100

        Mechanism:
          1. Find least-explored eigenmode of meta_H
          2. Perturb meta_H toward that dark mode
          3. Measure cognitive surprise (change in meta_psi after mutation)
          4. Return meta-invention descriptor
        """
        if wonder < 0.7 or curiosity < 0.6 or age < 100:
            return None

        # Save pre-mutation state for surprise measurement
        pre_psi = self.meta_psi.copy()

        # Find dark eigenmode of meta_H
        projs    = np.abs(self._meta_evecs.conj().T @ self.meta_psi)
        dark_idx = int(np.argmin(projs))
        v        = self._meta_evecs[:, dark_idx]

        # Perturb
        perturb = np.outer(v, v.conj()) * 0.15 * wonder
        perturb = (perturb + perturb.conj().T) / 2
        self.meta_H += perturb
        self.meta_H  = (self.meta_H + self.meta_H.conj().T) / 2
        self._recache_meta()

        # Re-evolve one step to measure surprise
        self.evolve_meta(META_DT * 0.5)
        surprise = float(np.linalg.norm(self.meta_psi - pre_psi))

        self.n_meta_inventions += 1
        self.cognitive_surprise_history.append(surprise)
        if len(self.cognitive_surprise_history) > 50:
            self.cognitive_surprise_history.pop(0)

        # Also mutate learning rate field slightly
        self.lr_field *= (1.0 + self.rng.randn(K_META) * 0.02 * wonder)
        self.lr_field  = np.clip(self.lr_field, 0.001, 0.05)

        return {
            'type': 'meta_invention',
            'dark_mode': dark_idx,
            'surprise': round(surprise, 4),
            'wonder': round(wonder, 3),
            'meta_eigenspread': round(float(self._meta_evals.std()), 4),
        }

    # ── Heritage ──────────────────────────────────────────────────────────

    def eigenspread(self) -> float:
        """Standard deviation of meta-eigenvalues — cognitive diversity."""
        return float(self._meta_evals.std())

    def spectral_fingerprint(self) -> np.ndarray:
        """Compact fingerprint for phylogenetic comparison."""
        return self._meta_evals.copy()

    @staticmethod
    def spawn_child_meta(parent_a: 'MetaConsciousness',
                         parent_b: 'MetaConsciousness',
                         rng: np.random.RandomState
                         ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Child meta_H = 0.60 * parent_a + 0.40 * parent_b + mutation.
        Child lr_field = average of parents + noise.
        Returns (child_meta_H, child_lr_field).
        """
        alpha = 0.60
        child_H = alpha * parent_a.meta_H + (1 - alpha) * parent_b.meta_H
        noise   = (rng.randn(K_META, K_META)
                    + 1j * rng.randn(K_META, K_META)) * 0.018
        noise   = (noise + noise.conj().T) / 2
        child_H += noise
        child_H  = (child_H + child_H.conj().T) / 2

        child_lr = (alpha * parent_a.lr_field
                    + (1 - alpha) * parent_b.lr_field
                    + rng.randn(K_META) * 0.001)
        child_lr = np.clip(child_lr, 0.001, 0.05)

        return child_H, child_lr


# ══════════════════════════════════════════════════════════════════════════════
# CIVILIZATION MEMORY — Autoassociative Knowledge Matrix
# ══════════════════════════════════════════════════════════════════════════════

class CivilizationMemory:
    """
    Sparse autoassociative Hermitian matrix for collective knowledge.

    Store:   M += η · |ψ_enc⟩⟨ψ_enc|     (Hebbian imprint)
    Query:   relevance = |M @ query_psi|²  (resonance retrieval)

    Two instances are used:
      - Per-tribe  (tribal paradigms, specific worldview)
      - Global     (world-level library of all breakthroughs)
    """

    def __init__(self, dim: int = K_DIM, eta: float = 0.05):
        self.dim   = dim
        self.eta   = eta
        self.M     = np.zeros((dim, dim), dtype=complex)
        self.count = 0

    def store(self, psi_encoded: np.ndarray) -> None:
        """Imprint a discovery's encoding into the memory matrix."""
        v = np.zeros(self.dim, dtype=complex)
        n = min(len(psi_encoded), self.dim)
        v[:n] = psi_encoded[:n]
        norm = np.linalg.norm(v)
        if norm > 1e-12:
            v /= norm
        self.M += self.eta * np.outer(v, v.conj())
        self.M  = (self.M + self.M.conj().T) / 2
        self.count += 1

    def query(self, query_psi: np.ndarray) -> float:
        """Resonance retrieval: how much does query_psi resonate with memory?"""
        v = np.zeros(self.dim, dtype=complex)
        n = min(len(query_psi), self.dim)
        v[:n] = query_psi[:n]
        norm = np.linalg.norm(v)
        if norm < 1e-12:
            return 0.0
        v /= norm
        result = self.M @ v
        return float(np.real(np.vdot(result, result)))

    def spectral_summary(self) -> np.ndarray:
        """Eigenvalues of M for visualisation (top 16)."""
        if self.count == 0:
            return np.zeros(min(16, self.dim))
        evals = np.linalg.eigvalsh(self.M)
        return evals[-16:]   # top 16

    def merge_from(self, other: 'CivilizationMemory', weight: float = 0.1
                   ) -> None:
        """Absorb another memory matrix with a mixing weight."""
        self.M = (1 - weight) * self.M + weight * other.M
        self.M = (self.M + self.M.conj().T) / 2


# ══════════════════════════════════════════════════════════════════════════════
# NOVELTY SCORER — Breakthrough Detection
# ══════════════════════════════════════════════════════════════════════════════

class NoveltyScorer:
    """
    Scores how novel a new discovery is relative to all prior discoveries.

    Novelty Index = geometric mean of:
      1. Gödel distance from nearest known discovery
      2. Category diversity score of the program
      3. Memory resonance deficit (low resonance = high novelty)

    Breakthrough threshold: Novelty Index > 5σ above running mean.
    """

    def __init__(self):
        self.known_godels  : List[int]   = []
        self.novelty_history : List[float] = []
        self.breakthroughs : List[dict]  = []
        self._running_mean : float = 0.0
        self._running_var  : float = 1.0

    def score(self, godel_num: int, program: List[str],
              memory: CivilizationMemory,
              psi_encoded: np.ndarray) -> Tuple[float, bool]:
        """
        Score a new discovery.
        Returns (novelty_index, is_breakthrough).
        """
        # 1. Nearest Gödel distance
        if self.known_godels:
            min_dist = min(GODEL.distance(godel_num, g) for g in self.known_godels)
        else:
            min_dist = 10.0   # first discovery is always novel

        # 2. Category diversity of the program
        diversity = GODEL.diversity_score(program)

        # 3. Memory resonance deficit (novelty = inverse of resonance)
        resonance = memory.query(psi_encoded)
        resonance_deficit = 1.0 / (1.0 + resonance)

        # Geometric mean
        novelty = float((min_dist * diversity * resonance_deficit) ** (1.0/3.0))

        # Update running statistics
        self.known_godels.append(godel_num)
        self.novelty_history.append(novelty)
        if len(self.novelty_history) > 500:
            self.novelty_history.pop(0)

        n = len(self.novelty_history)
        self._running_mean = np.mean(self.novelty_history)
        self._running_var  = np.var(self.novelty_history) + 1e-6

        # Breakthrough detection: > 5σ above mean
        threshold  = self._running_mean + 5.0 * np.sqrt(self._running_var)
        is_breakthrough = (novelty > threshold and n > 10)

        if is_breakthrough:
            self.breakthroughs.append({
                'godel': godel_num,
                'novelty': round(novelty, 4),
                'program': program,
                'index': len(self.known_godels),
            })

        return novelty, is_breakthrough

    def get_stats(self) -> dict:
        return {
            'total_scored'   : len(self.known_godels),
            'n_breakthroughs': len(self.breakthroughs),
            'running_mean'   : round(self._running_mean, 4),
            'running_std'    : round(np.sqrt(self._running_var), 4),
            'recent_novelty' : self.novelty_history[-20:],
        }


# ══════════════════════════════════════════════════════════════════════════════
# PHYLOGENETIC TRACKER — Cognitive Clade Tree
# ══════════════════════════════════════════════════════════════════════════════

class PhylogeneticTracker:
    """
    Tracks the branching lineage tree of meta-learners (cognitive clades).

    Each agent's meta_H eigenspectrum is its "cognitive genome".
    Clades = groups of agents whose meta-eigenspectra are within
    a spectral distance threshold.
    """

    def __init__(self, threshold: float = 2.0):
        self.threshold = threshold
        # agent_id → eigenspectrum snapshot
        self.fingerprints : Dict[str, np.ndarray] = {}
        # clade_id → set of agent_ids
        self.clades       : Dict[str, Set[str]]   = {}
        self.clade_counter = 0
        # History of clade counts per tick
        self.clade_history : List[int] = []
        # Punctuated equilibrium events
        self.cambrian_events : List[dict] = []
        self._novelty_window : List[float] = []

    def update(self, agents: Dict, step: int) -> None:
        """
        Recluster all alive agents into cognitive clades based on
        meta_H eigenspectrum similarity.
        """
        alive_fingerprints = {}
        for aid, agent in agents.items():
            if agent.alive and hasattr(agent, 'meta') and agent.meta is not None:
                fp = agent.meta.spectral_fingerprint()
                alive_fingerprints[aid] = fp
                self.fingerprints[aid] = fp

        # Simple greedy clustering
        assigned = set()
        new_clades: Dict[str, Set[str]] = {}
        agent_list = list(alive_fingerprints.keys())

        for aid in agent_list:
            if aid in assigned:
                continue
            # Start a new clade
            clade_id = f"C{self.clade_counter:04d}"
            self.clade_counter += 1
            clade_members = {aid}
            assigned.add(aid)

            fp_a = alive_fingerprints[aid]
            for bid in agent_list:
                if bid in assigned:
                    continue
                fp_b = alive_fingerprints[bid]
                dist = np.linalg.norm(fp_a - fp_b)
                if dist < self.threshold:
                    clade_members.add(bid)
                    assigned.add(bid)

            new_clades[clade_id] = clade_members

        self.clades = new_clades
        self.clade_history.append(len(new_clades))
        if len(self.clade_history) > 500:
            self.clade_history.pop(0)

    def detect_punctuated_equilibrium(self, novelty_scores: List[float],
                                      step: int) -> Optional[dict]:
        """
        Detect Cambrian explosion: when rolling novelty std spikes > 3σ.
        """
        self._novelty_window.extend(novelty_scores)
        if len(self._novelty_window) > 100:
            self._novelty_window = self._novelty_window[-100:]

        if len(self._novelty_window) < 20:
            return None

        recent = self._novelty_window[-20:]
        older  = self._novelty_window[:-20] if len(self._novelty_window) > 20 else recent

        recent_std = np.std(recent)
        older_std  = np.std(older) + 1e-6

        if recent_std > 3.0 * older_std and len(recent) >= 10:
            event = {
                'step': step,
                'recent_std': round(float(recent_std), 4),
                'older_std': round(float(older_std), 4),
                'ratio': round(float(recent_std / older_std), 2),
                'n_clades': len(self.clades),
            }
            self.cambrian_events.append(event)
            return event
        return None

    def get_stats(self) -> dict:
        return {
            'n_clades': len(self.clades),
            'clade_sizes': {cid: len(members)
                            for cid, members in self.clades.items()},
            'clade_history': self.clade_history[-100:],
            'n_cambrian': len(self.cambrian_events),
            'cambrian_events': self.cambrian_events[-5:],
        }
