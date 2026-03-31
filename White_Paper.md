White Paper: Riemannian Wave Classifier (RWC) and Geometric Wave Learner (GWL)

Abstract

This white paper gives a compact but technically serious summary of two GPU-accelerated classifiers: Riemannian Wave Classifier (RWC) and Geometric Wave Learner (GWL). The project treats classification as a geometric resonance problem on a learned manifold rather than a standard decision-boundary problem. Using the EEG Eye State dataset (OpenML 1471), the framework evolves from a baseline configuration to a final polychromatic ensemble that reaches 93.27% accuracy on GWL, improving from 67.46% in the earliest version. The method combines graph geometry, spectral analysis, class potentials, discrete Ricci flow, and a holographic radial frequency kernel.

1. What This Work Is

This is a white paper, not the full research manuscript. It is meant to explain the idea clearly and briefly while preserving the important technical content. The focus is on:

the problem being solved,

the structure of the method,

the data and preprocessing,

the main mathematical components,

the version history from V1 to V13,

and the final performance outcome.


2. Core Idea

RWC and GWL both classify data by studying how a sample resonates with the geometry of the training manifold.

RWC builds a static graph manifold, computes its Laplacian spectrum, injects class-specific potentials, and classifies by resonance energy.

GWL starts from the same manifold idea but also applies label-driven discrete Ricci flow so that the graph geometry itself is warped to separate classes more clearly.

Later versions add a Holographic Radial Frequency (HRF) kernel and a polychromatic ensemble to combine several geometric views of the same problem.


In simple terms, the system does not ask only “what is the best boundary?” It asks “which class does this point resonate with most strongly on the manifold?”

3. Dataset and Preprocessing

The benchmark is the EEG Eye State dataset from OpenML.

Property	Value

Dataset	EEG Eye State
OpenML ID	1471
Samples	14,980
Raw inputs	14 EEG channels
Task	Binary classification
Target	Eyes open / eyes closed


The preprocessing pipeline expands the raw EEG into a richer 78-dimensional representation:

1. Clipping of extreme values to reduce artifacts.


2. Bipolar montage to capture inter-channel differences.


3. Spectral FFT features to add frequency-domain structure.


4. Robust scaling to reduce the effect of outliers.



Final processed shape: (14980, 78).

4. Main Mathematical Framework

4.1 Graph Construction

A k-nearest-neighbor graph is built from the training data. Edge weights use a Zelnik-Manor self-tuning Gaussian bandwidth, which adapts to local density instead of using one global scale.

This matters because EEG data is not uniformly distributed. Dense regions and sparse regions need different effective radii.

4.2 Graph Laplacian

The graph is converted into a symmetric normalized Laplacian:

L = I - D^{-1/2} W D^{-1/2}

Its eigendecomposition produces the spectral basis of the manifold:

eigenvectors = geometric modes,

eigenvalues = structural frequencies.


4.3 Class Potentials and Resonance

RWC adds a class-conditional potential to the manifold and forms a perturbed Hamiltonian:

H^(c) = L + V^(c)

Query points are projected into the spectral basis, and the final class score is computed from a Lorentzian resonance energy. The class with the strongest resonance wins.

4.4 Label-Driven Ricci Flow

GWL evolves the graph weights with discrete Ricci flow. Same-class edges are strengthened and different-class edges are weakened, so the manifold becomes more class-separated before spectral analysis.

This is the main geometric difference between GWL and RWC.

4.5 HRF Kernel

Later versions add a Holographic Radial Frequency kernel:

Psi(d) = exp(-gamma * d^2) * (1 + cos(omega * d))

This captures local oscillatory structure that the global spectral model may miss.

4.6 Polychromatic Forests

The final version uses polychromatic forests. Each tree receives a different spectral configuration, so the ensemble sees several “colors” of the same manifold. The trees are diverse by:

frequency,

damping,

neighborhood size.


Their predictions are aggregated by majority vote.

5. Version History

The notebook develops through V1 to V13.

V1 — Baseline

A smaller spectral basis and a simplified energy calculation were used. This version was weak but established the initial pipeline.

Results: RWC 70.03%, GWL 67.46%.

V2 — Holographic Energy Fix

This was the major breakthrough. The energy calculation was corrected so that class structure was preserved at the sample level instead of being collapsed into one vector. The spectral basis was enlarged and the graph parameters were improved.

Results: RWC 83.18%, GWL 89.55%.

V3 — Evaluation Correction

The evaluation protocol was standardized with a 75/25 split. This made the benchmark more consistent.

Results: RWC 84.73%, GWL 90.33%.

V4 — Architectural Cleanup

The implementation was reorganized without changing the core math. This version served as the cleaner reference version.

Results: unchanged from V3.

V5 — HRF Integration

The HRF kernel was introduced. This added local frequency texture on top of the global manifold structure.

Results: RWC 91.40%, GWL 92.63%.

V13 — Final Polychromatic Version

The final version improved HRF handling, tightened local query search, and combined multiple spectral views in an ensemble.

Results: RWC 93.00%, GWL 93.27%.

6. Performance Summary

Version	RWC	GWL

V1	70.03%	67.46%
V2	83.18%	89.55%
V3	84.73%	90.33%
V4	84.73%	90.33%
V5	91.40%	92.63%
V13	93.00%	93.27%


The total improvement for GWL is +25.81 percentage points from the baseline to the final version.

7. What the Results Mean

The strongest gains came from three ideas:

1. Fixing the resonance energy computation so class structure was not collapsed.


2. Making the manifold richer through better graph and spectral settings.


3. Adding local frequency texture through HRF and then combining multiple spectral views in an ensemble.



The result is a classifier that is not just fitting labels, but modeling the geometry of the data.

8. GPU Implementation

The full system is built for Python 3.11 on an NVIDIA T4 GPU using CuPy and cuML.

Main GPU operations include:

k-NN graph construction,

sparse weight assembly,

Laplacian eigendecomposition,

batched resonance energy computation,

Ricci flow updates,

and ensemble inference.


This makes the otherwise expensive manifold operations practical on the full dataset.

9. Limitations

The framework is powerful but expensive. Its main limitations are:

heavy graph construction cost,

eigendecomposition cost,

Ricci flow sensitivity,

strong dependence on hyperparameters,

and large runtime when using full-data settings.


Fast compressed test versions can be misleading if they remove too much geometric structure.

10. Conclusion

RWC and GWL form a geometry-first classification framework for EEG eye-state detection. The final system combines graph Laplacians, class potentials, Ricci flow, HRF kernels, and polychromatic ensembles into one coherent pipeline. The best reported result is 93.27% accuracy on GWL, showing that the approach is both technically distinctive and empirically strong.

The main message is simple: the model improves when the geometry of the data is preserved, refined, and viewed through multiple spectral scales.

Reference Note

This white paper is based on the research README describing the EEG Eye State benchmark, the full V1–V13 iteration path, the Laplacian and Hamiltonian formulation, the Ricci-flow extension, the HRF kernel, and the final polychromatic ensemble design. fileciteturn1file0
