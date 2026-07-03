# DeepAnalyze-StatASkills

DeepAnalyze-StatASkills integrates the statistical toolkit from **StatABench** into the **DeepAnalyze** data science agent framework.

The goal is simple: when DeepAnalyze writes and executes analysis code, it can call a curated statistical toolkit through a stable Python interface instead of re-implementing statistical tests, regression models, survival analysis, time-series methods, A/B testing, or causal inference from scratch.

```python
from stataskills import run_tool, list_tools, tool_help

df = run_tool("read_csv", file="hospital_stay.csv")
result = run_tool(
    "multivariable_linear_regression",
    data=df,
    y_col="Length_of_Stay_days",
    x_cols=["Patient_Age", "Severity_Score", "Is_Surgical"],
)
```

## What Is Included

```text
DeepAnalyze/          # DeepAnalyze API and WebUI v2 with stataskills instruction injection
stataskills_demo/     # stataskills package, demo prompts, datasets, reports, and validation scripts
```

The integration is intentionally lightweight. The DeepAnalyze WebUI is kept unchanged; the main framework change is in `DeepAnalyze/API/utils.py`, where a system instruction tells the agent to prefer `stataskills.run_tool(...)` for statistical analysis.

## StatASkills

`stataskills` packages the statistical functions from StatABench as a Python toolkit for code-execution agents.

It exposes three primary interfaces:

```python
from stataskills import run_tool, list_tools, tool_help
```

Covered capabilities include:

- data loading, descriptive statistics, missing-value checks, and outlier detection
- correlation analysis and hypothesis testing
- linear regression, multivariable regression, GLM, and robust regression
- time-series stationarity tests and STL decomposition
- Kaplan-Meier, log-rank test, and Cox model
- A/B testing, bootstrap confidence intervals, and power analysis
- Bayesian analysis and causal inference, including DID, PSM, and synthetic control

## Quick Start

### 1. Install dependencies

```bash
cd DeepAnalyze
pip install -r requirements.txt

cd ../stataskills_demo
pip install -e ".[full]"
```

### 2. Start the DeepAnalyze model service

```bash
vllm serve RUC-DataLab/DeepAnalyze-8B \
  --host 0.0.0.0 \
  --port 8000
```

You can also replace `RUC-DataLab/DeepAnalyze-8B` with a local model path.

### 3. Start the DeepAnalyze API

```bash
cd DeepAnalyze/API
python start_server.py
```

Default endpoints:

- DeepAnalyze API: `http://localhost:8200`
- File server: `http://localhost:8100`
- vLLM endpoint: `http://localhost:8000/v1`

### 4. Run the demos

```bash
cd stataskills_demo
python examples/run_deepanalyze_demo_tasks.py --task all
```

Generated reports are saved under:

```text
stataskills_demo/artifacts/reports/
```

## Examples

This repository includes three reproducible examples:

| Task | Scenario | Observed stataskills usage |
|---|---|---|
| `hospital` | Hospital operations and ER pressure | `linear_regression` / `correlation_analysis` style calls |
| `growth` | Product growth and conversion experiment | A/B-style tests and data quality checks |
| `policy` | Policy effect evaluation | regression/DID-style analysis on policy panel data |

Each example includes:

- a natural-language prompt
- the required CSV datasets
- the original DeepAnalyze report
- raw model output and validation files

The prompts are intentionally short and human-like. They do not include required code blocks or a tool checklist. Validation only checks that DeepAnalyze really called `stataskills.run_tool(...)` at least once and produced a non-empty report; warnings preserve model trial-and-error such as attempted unknown tool names.

## Validate the Toolkit

```bash
cd stataskills_demo
python scripts/verify_stataskills_all_tools.py
```

Expected result:

```text
Total cases: 55
Passed: 55
Failed: 0
Public tools covered by primary PASS: 38 / 38
```

## Acknowledgements

This project builds on:

- **DeepAnalyze** by RUC-DataLab: https://github.com/ruc-datalab/DeepAnalyze
- **StatABench**: https://github.com/youxin01/StatABench

We thank the authors of both projects. This repository extracts and packages the statistical toolkit from StatABench and integrates it into the DeepAnalyze framework for reproducible agentic statistical analysis.

## License

DeepAnalyze is released under the MIT License. StatABench is released under GPLv3. Because this repository includes and adapts StatABench toolkit code, the root license of this integrated repository is GPLv3.

See:

- `LICENSE`
- `THIRD_PARTY_LICENSES/DeepAnalyze-MIT-LICENSE`
- `THIRD_PARTY_LICENSES/StatABench-GPLv3-LICENSE`
