# DeepAnalyze-StatASkills

DeepAnalyze-StatASkills integrates the statistical toolkit from **StatABench** into the **DeepAnalyze** data science agent framework.

It is built on the [DeepAnalyze paper](https://arxiv.org/abs/2510.16872) and the [StatABench paper](https://arxiv.org/abs/2606.22977).

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

### Featured Example: A/B Experiment

**Prompt**

> 我上传了 `conversion_data.csv` 和 `website_session_data.csv`。
>
> 我们最近做了一个 A/B 实验，想知道 B 组是否值得继续放量。请帮我看转化率和用户参与度有没有明显差异，并给出下一步建议。
>
> 如果系统里有现成的统计分析工具，请直接用它们来判断差异，不用自己手写检验。
>
> 请用中文回答，结论别说得过度绝对。

**Report preview**

The preview below is rendered directly from the unedited DeepAnalyze Markdown report.

![A/B experiment report preview](docs/assets/growth-report-preview.png)

DeepAnalyze produced this report from the short prompt above and the uploaded CSV files. The raw trace shows actual `stataskills.run_tool(...)` calls, including `read_csv`, `check_missing_values`, and `ab_ttest`.

Open the full example:

- Prompt: [`deepanalyze_growth_task.md`](stataskills_demo/examples/deepanalyze_growth_task.md)
- Report: [`growth.md`](stataskills_demo/artifacts/reports/growth.md)
- Raw model trace: [`growth_raw.md`](stataskills_demo/artifacts/reports/growth_raw.md)
- Validation: [`growth_validation.json`](stataskills_demo/artifacts/reports/growth_validation.json)

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

## Related Projects and Papers

This project builds on:

- **DeepAnalyze** by RUC-DataLab
  - Code: [https://github.com/ruc-datalab/DeepAnalyze](https://github.com/ruc-datalab/DeepAnalyze)
  - Paper: [https://arxiv.org/abs/2510.16872](https://arxiv.org/abs/2510.16872)
- **StatABench**
  - Code: [https://github.com/youxin01/StatABench](https://github.com/youxin01/StatABench)
  - Paper: [https://arxiv.org/abs/2606.22977](https://arxiv.org/abs/2606.22977)

This repository extracts and packages the statistical toolkit from StatABench and integrates it into the DeepAnalyze framework for reproducible agentic statistical analysis.

## License

DeepAnalyze is released under the MIT License. StatABench is released under GPLv3. Because this repository includes and adapts StatABench toolkit code, the root license of this integrated repository is GPLv3.

See:

- `LICENSE`
- `THIRD_PARTY_LICENSES/DeepAnalyze-MIT-LICENSE`
- `THIRD_PARTY_LICENSES/StatABench-GPLv3-LICENSE`
