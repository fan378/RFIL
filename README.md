# Removing First, Infilling Later: Decoupling Environment-Dependent Facts to Mitigate Hallucinations in Clinical Discharge Summaries

## Introduction

Large language models (LLMs) have shown great potential in generating electronic medical records (EMRs). However, current LLMs are often not fully aligned with medical writing conventions, and they tend to produce factual hallucinations that misalign with the structure and logic of EMR generation, reducing output consistency and controllability.

To tackle these issues, we introduce **RFIL** (Removing-First, Infilling-Later), a multi-stage framework designed to decouple medical narrative generation from the instantiation of environment-dependent facts. The framework operates in three stages:

1. **Data Cleaning and Normalization**: The EMR corpus is cleaned to reduce structural noise and inconsistencies.
2. **Placeholder Generation**: Entities with strong real-world constraints are replaced with placeholders to help guide narrative generation.
3. **Controlled Backfilling**: A backfilling model restores the removed entities while adhering to clinical workflow constraints, ensuring accurate and fluent output.

We evaluate the generation quality based on **core fact coverage** and **hallucination rate**. Experiments on a Chinese dataset and MIMIC-IV v3.0 demonstrate that RFIL improves factual consistency and reduces hallucinations, providing a more reliable approach to EMR generation.

![RFIL Framework](figures/framework.png)

