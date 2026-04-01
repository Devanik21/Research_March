

---

# White Paper

## Riemannian Wave Classifier (RWC) & Geometric Wave Learner (GWL)

### A Geometry–Wave Hybrid Framework for EEG Eye-State Classification

---

## Executive Summary

This white paper presents a concise and clear overview of two hybrid machine learning algorithms: **Riemannian Wave Classifier (RWC)** and **Geometric Wave Learner (GWL)**. These methods approach classification as a **geometric resonance problem on a data manifold** rather than a traditional decision-boundary optimization problem.

The framework was developed and tested on the **EEG Eye State dataset** and evolved through multiple versions (V1 to V13), improving performance from **~67% to ~93.27% accuracy**. The system combines **graph geometry, spectral analysis, class potentials, Ricci flow, and wave-based kernels** into a unified classification framework.

This document summarizes the full idea, architecture, iteration history, and results in a shorter and simpler format than the main research paper.

---

## 1. Introduction

Traditional machine learning classifiers learn decision boundaries directly in feature space. The RWC–GWL framework instead assumes that:

> Data lies on a geometric manifold, and classification should be based on how a sample interacts with the geometry of that manifold.

Instead of asking *"Which side of the boundary is this sample on?"*, the framework asks:

> *"Which class geometry does this sample resonate with more strongly?"*

This leads to a hybrid system combining **graph theory, spectral methods, curvature flow, and wave physics concepts**.

---

## 2. Dataset and Feature Engineering

### Dataset

* **Dataset:** EEG Eye State
* **Samples:** 14,980
* **Channels:** 14 EEG channels
* **Task:** Binary classification (Eyes Open vs Eyes Closed)

### Feature Engineering Pipeline

The raw EEG signals are transformed into a richer feature space:

1. **Signal clipping** – removes extreme artifacts.
2. **Bipolar montage** – captures differences between EEG channels.
3. **FFT spectral features** – adds frequency-domain information.
4. **Robust scaling** – reduces the effect of outliers.

**Final processed feature space:** 78 dimensions.

This step is critical because the geometric model depends heavily on feature quality.

---

## 3. Mathematical Framework

### 3.1 Graph Construction

A **k-nearest neighbor (k-NN) graph** is built from the training data. Edge weights are computed using a **self-tuning Gaussian kernel**, which adapts to local data density.

This allows the graph to represent both dense and sparse regions properly.

---

### 3.2 Graph Laplacian and Spectral Basis

The graph is converted into a **normalized Laplacian matrix**:

```
L = I − D^{-1/2} W D^{-1/2}
```

Where:

* W = weight matrix
* D = degree matrix
* L = graph Laplacian

The eigenvectors of the Laplacian form the **spectral basis of the manifold**, representing geometric vibration modes of the data.

---

### 3.3 Riemannian Wave Classifier (RWC)

RWC introduces **class-specific potentials** into the manifold:

```
H^(c) = L + V^(c)
```

Where:

* L = Laplacian
* V^(c) = class potential
* H^(c) = class-specific Hamiltonian

A query point is projected into the spectral space and evaluated using a **resonance energy function**. The class producing the strongest resonance is selected.

This turns classification into a **wave–energy matching problem**.

---

### 3.4 Geometric Wave Learner (GWL)

GWL extends RWC by applying **label-driven discrete Ricci flow** to the graph before spectral analysis.

Ricci flow modifies graph edge weights so that:

* Same-class points move closer.
* Different-class points move further apart.

This means GWL **learns the geometry itself**, not just the classifier.

---

### 3.5 Holographic Radial Frequency (HRF) Kernel

A later improvement adds a kernel of the form:

```
Ψ(d) = exp(−γ d²) · (1 + cos(ω d))
```

This kernel captures:

* Local decay (Gaussian part)
* Oscillatory structure (cosine part)

This adds **local texture information** to the global manifold model.

---

### 3.6 Polychromatic Forests

The final system uses multiple spectral configurations in an ensemble called a **Polychromatic Forest**.

Each model uses different:

* spectral frequencies,
* damping factors,
* neighborhood sizes.

The ensemble combines multiple geometric views of the same data.

---

## 4. Version Development (V1 → V13)

| Version | RWC    | GWL    | Key Change                   |
| ------- | ------ | ------ | ---------------------------- |
| V1      | 70.03% | 67.46% | Initial manifold + resonance |
| V2      | 83.18% | 89.55% | Correct energy computation   |
| V3      | 84.73% | 90.33% | Proper evaluation split      |
| V4      | 84.73% | 90.33% | Code architecture cleanup    |
| V5      | 91.40% | 92.63% | HRF kernel added             |
| V13     | 93.00% | 93.27% | Polychromatic ensemble       |

**Total improvement (GWL): +25.81 percentage points**.

The largest improvement came from fixing the **resonance energy formulation** and later from adding **HRF + ensemble diversity**.

---

## 5. GPU Implementation

The system is implemented using:

* Python 3.11
* CuPy
* cuML
* NVIDIA T4 GPU

GPU acceleration is used for:

* k-NN graph construction
* Laplacian eigendecomposition
* Ricci flow updates
* Resonance energy computation
* Ensemble inference

Without GPU acceleration, the manifold computations would be very slow.

---

## 6. Key Insights from the Research

The performance improvements across versions show that accuracy increased when:

1. The **spectral energy calculation** was corrected.
2. The **manifold resolution** was increased.
3. The **geometry was allowed to evolve** (Ricci flow).
4. **Local oscillatory structure** was added (HRF).
5. **Multiple spectral views** were combined (ensemble).

This suggests the model works best when it captures both **global geometry** and **local texture**.

---

## 7. Limitations

The system still has several challenges:

* High computational cost
* Expensive eigendecomposition
* Sensitive hyperparameters
* Ricci flow stability issues
* Long runtime on full dataset

Fast compressed versions often lose too much geometric information and therefore underperform.

---

## 8. Conclusion

The RWC–GWL framework represents a **geometry-first approach to machine learning classification**. Instead of learning only decision boundaries, the system learns the **shape of the data manifold** and classifies samples based on **wave resonance within that geometry**.

The final system combines:

* Graph Laplacian geometry
* Class potentials
* Ricci flow
* HRF kernel
* Polychromatic ensemble

The best achieved result is **93.27% accuracy**, showing that the approach is both mathematically unique and empirically strong.

---

## 9. Future Direction

The most promising future improvements are likely to come from:

* Better manifold compression instead of full graph computation
* Residual correction for hard samples
* Improved class-conditional geometry
* Hybrid ensemble of RWC and GWL variants
* Decision threshold optimization

The long-term goal is to push the framework beyond the current performance while preserving its geometric foundation.

---

**End of White Paper**
