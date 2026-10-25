# Demo walkthrough

The 55-second MP4 is a captioned walkthrough assembled from genuine browser screenshots captured while exercising the running Python application. It uses slow vertical pans through full-page captures and successive live-monitor states. It has no audio and is not a continuous desktop recording. No UI or analytical results are fabricated.

The upgraded screenshots show fitted model inference, product recommendations, source retrieval and an explicitly synthetic experiment. The local API and public browser engine share the same model contracts. Observational metrics and commercial scenarios are not measured campaign impact.

| Time | Screen | Explanation |
| --- | --- | --- |
| 00–06s | 01 / Marketing decision workspace | Connect shopper evidence to a commercial hypothesis and a controlled test. |
| 06–14s | 02 / Supervised repurchase model | November top-20% precision: 67.8% forest vs 63.4% RFM. Historical, not causal. |
| 14–19s | 03 / Actual fitted-model inference | Changing a coherent behavior profile recalculates the probability and model-path drivers. |
| 19–27s | 04 / Learned product factors | SVD hit-rate@5: 27.9% vs 14.4% popularity among eligible novel-product shoppers. |
| 27–35s | 05 / Read the contribution outcome | Synthetic example: conversion improves, but the contribution interval crosses zero. |
| 35–43s | 06 / Source-backed evidence retrieval | Fitted TF-IDF retrieval returns existing passages and sources; it is not a generative LLM. |
| 43–49s | 07 / Commercial assumptions made explicit | Include discounts on baseline purchases, break-even conversion and test sample size. |
| 49–55s | 08 / Auditable evidence and limits | 50 Python checks plus browser-engine reference tests. No invented campaign results. |

Files: `assets/brandscope-demo.mp4`, `assets/brandscope-preview.gif`, `assets/brandscope-demo.srt`. Full application screenshots and a mobile capture are in the same assets folder.

To reproduce the workflow interactively: use the README's two-minute tour, run `python server.py`, change the discount, save a scenario, download a brief, then send events from Activation monitor. Actual captures are from 25 October 2026.
