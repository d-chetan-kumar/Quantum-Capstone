# Variational Quantum Classifier (VQC) Methodology

## Overview
This document outlines the pipeline for the quantum machine learning component of the fraud detection platform. The VQC is implemented using Qiskit.

## Quantum Algorithm Pipeline
1. **Dataset Selection & Validation**: Ensuring data is suitable for quantum encoding.
2. **Preprocessing & Feature Engineering**: Dimensionality reduction (e.g., PCA) to fit data into available qubits.
3. **Feature Encoding**: Mapping classical data into quantum states using a Quantum Feature Map (e.g., ZZFeatureMap).
4. **Variational Circuit (Ansatz)**: Parameterized quantum circuit (e.g., RealAmplitudes) defining the trainable layers. Entanglement strategies are applied here.
5. **Measurement**: Extracting classical values from the quantum state.
6. **Optimizer**: Classical optimization algorithm (e.g., COBYLA, SPSA) to update the ansatz parameters during training.

## Hybrid Risk Engine
- The final architecture runs classical models and the VQC in parallel.
- A blending or ensemble mechanism (Hybrid Engine) combines both probabilities to output a final `hybrid_probability`.

## Academic & Evaluation Requirements
For the capstone review, the platform will generate:
- Circuit diagrams of the actual implemented VQC.
- Training loss curves.
- Confusion matrices, ROC, and PR curves comparing Classical vs. Quantum vs. Hybrid models.
- Time and space complexity analysis of the quantum circuit (depth, number of parameters).
