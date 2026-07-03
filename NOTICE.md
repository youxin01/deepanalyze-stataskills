# Notice

This repository is a redistribution and integration package for demonstration and reproducibility.

## Upstream Projects

- DeepAnalyze: https://github.com/ruc-datalab/DeepAnalyze
  - Original copyright: RUC-DataLab
  - License: MIT License
  - Included mainly under `DeepAnalyze/`

- StatABench: https://github.com/youxin01/StatABench
  - License: GNU General Public License v3.0
  - Statistical functions were packaged as `stataskills` under `stataskills_demo/stataskills/`

## Local Integration Changes

- Added a DeepAnalyze API prompt injection that tells the model to use `stataskills.run_tool(...)` for statistical analysis when possible.
- Packaged selected StatABench statistical functions as a Python package named `stataskills`.
- Added three reproducible DeepAnalyze demo tasks with datasets, prompts, original reports, raw outputs, and validation files.

The DeepAnalyze WebUI v2 source is included unchanged from the local DeepAnalyze copy.
