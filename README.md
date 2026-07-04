# DeepAnalyze-StatASkills

[DeepAnalyze](https://github.com/ruc-datalab/DeepAnalyze) with a bundled
StatASkills statistical toolkit from
[StatABench](https://github.com/youxin01/StatABench).

This project lets DeepAnalyze use a stable Python toolkit for common statistical
work instead of re-implementing tests, regressions, A/B analysis, time-series
methods, survival analysis, Bayesian analysis, and causal inference from
scratch during code execution.

- DeepAnalyze paper: [arXiv:2510.16872](https://arxiv.org/abs/2510.16872)
- StatABench paper: [arXiv:2606.22977](https://arxiv.org/abs/2606.22977)

## Highlights

- Supports both the OpenAI-compatible DeepAnalyze API and WebUI v2.
- Provides `stataskills.run_tool(...)`, `list_tools()`, and `tool_help(...)`.
- Covers 38 public statistical tools packaged from StatABench functions.
- Includes reproducible prompts, datasets, raw model traces, reports, and
  validation files.
- Keeps the integration lightweight: no MCP protocol or new tool-calling
  runtime is required.

## Repository Layout

```text
DeepAnalyze/          # DeepAnalyze API and WebUI v2 source
stataskills_demo/     # stataskills package, datasets, examples, and reports
docs/assets/          # README preview assets
```

Key integration files:

```text
DeepAnalyze/API/utils.py
DeepAnalyze/demo/chat_v2/backend_app/services/chat.py
DeepAnalyze/demo/chat_v2/backend_app/services/execution.py
```

DeepAnalyze appends a short instruction after its normal `# Instruction` and
`# Data` blocks telling the model to prefer:

```python
from stataskills import run_tool, list_tools, tool_help
```

For details, see
[`stataskills_demo/docs/deepanalyze_stataskills_integration.md`](stataskills_demo/docs/deepanalyze_stataskills_integration.md).

## Installation

```bash
git clone git@github.com:youxin01/deepanalyze-stataskills.git
cd deepanalyze-stataskills

pip install -r DeepAnalyze/requirements.txt
pip install -e "stataskills_demo[full]"
```

For the WebUI, install frontend dependencies once:

```bash
cd DeepAnalyze/demo/chat_v2/frontend
npm install
```

## Choose a Way to Run

There are two entrypoints. You usually need only one of them:

| Entrypoint | Use it when | Start command |
|---|---|---|
| WebUI v2 | You want to upload files and interact in a browser. | `cd DeepAnalyze/demo/chat_v2 && bash start.sh` |
| DeepAnalyze API | You want scripts, batch runs, benchmarks, or automated report generation. | `cd DeepAnalyze/API && python start_server.py` |

Both entrypoints use a model endpoint such as `http://localhost:8000/v1`. Do not
start both on the same default port unless you change one of their ports.

## 1. Start a Model

DeepAnalyze expects an OpenAI-compatible model endpoint at
`http://localhost:8000/v1`.

Example with a local DeepAnalyze-8B checkpoint:

```bash
python -m vllm.entrypoints.openai.api_server \
  --model /path/to/DeepAnalyze-8B \
  --served-model-name DeepAnalyze-8B \
  --host 0.0.0.0 \
  --port 8000 \
  --max-model-len 16384 \
  --trust-remote-code
```

You can also use another OpenAI-compatible provider through WebUI v2's
`Custom Model` option.

## 2A. Run WebUI v2

```bash
cd DeepAnalyze/demo/chat_v2
cp .env.example .env
bash start.sh
```

Open:

```text
http://localhost:4000
```

In the left panel:

- choose `Local` if your model is running at `http://localhost:8000/v1`;
- choose `Custom Model` for another OpenAI-compatible API provider.

For WebUI usage, you do not need to start `DeepAnalyze/API/start_server.py`.
WebUI v2 has its own backend in `DeepAnalyze/demo/chat_v2/backend.py`.

## 2B. Run DeepAnalyze API

```bash
cd DeepAnalyze/API
python start_server.py
```

Default services:

```text
DeepAnalyze API: http://localhost:8200
File server:     http://localhost:8100
Model endpoint:  http://localhost:8000/v1
```

This API entrypoint is for programmatic use: batch reports, benchmark scripts,
or integrating DeepAnalyze-StatASkills into another backend. It is not required
for browser WebUI usage.

## Run Examples

The repository includes three reproducible tasks:

| Task | Scenario | Main statistical use |
|---|---|---|
| `growth` | Product A/B experiment | A/B tests and data quality checks |
| `hospital` | Hospital operations | correlation and regression analysis |
| `policy` | Policy effect evaluation | DID-style causal analysis |

Run one task:

```bash
cd stataskills_demo
python examples/run_deepanalyze_demo_tasks.py --task growth
```

Run all tasks:

```bash
python examples/run_deepanalyze_demo_tasks.py --task all
```

Reports and raw traces are saved under:

```text
stataskills_demo/artifacts/reports/
```

These report examples use the DeepAnalyze API entrypoint, so start
`DeepAnalyze/API/start_server.py` before running them.

Validate the WebUI backend path:

```bash
python examples/run_webui_stataskills_demo.py --task growth
```

This validation uses the WebUI backend, so start `DeepAnalyze/demo/chat_v2`
before running it.

## Featured Example

Prompt:

> I uploaded `conversion_data.csv` and `website_session_data.csv`.
>
> We recently ran an A/B experiment and want to know whether group B is worth
> rolling out further. Please check whether conversion and engagement differ
> noticeably, and give a next-step recommendation.

The preview below is rendered directly from the unedited DeepAnalyze Markdown
report.

![A/B experiment report preview](docs/assets/growth-report-preview.png)

Open the full example:

- Prompt: [`deepanalyze_growth_task.md`](stataskills_demo/examples/deepanalyze_growth_task.md)
- Report: [`growth.md`](stataskills_demo/artifacts/reports/growth.md)
- Raw model trace: [`growth_raw.md`](stataskills_demo/artifacts/reports/growth_raw.md)
- Validation: [`growth_validation.json`](stataskills_demo/artifacts/reports/growth_validation.json)

## Validate StatASkills

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

## Related Projects

- DeepAnalyze
  - Code: [https://github.com/ruc-datalab/DeepAnalyze](https://github.com/ruc-datalab/DeepAnalyze)
  - Paper: [https://arxiv.org/abs/2510.16872](https://arxiv.org/abs/2510.16872)
- StatABench
  - Code: [https://github.com/youxin01/StatABench](https://github.com/youxin01/StatABench)
  - Paper: [https://arxiv.org/abs/2606.22977](https://arxiv.org/abs/2606.22977)

## License

DeepAnalyze is released under the MIT License. StatABench is released under
GPLv3. Because this repository includes and adapts StatABench toolkit code, this
integrated repository is released under GPLv3.

See:

- [`LICENSE`](LICENSE)
- [`THIRD_PARTY_LICENSES/DeepAnalyze-MIT-LICENSE`](THIRD_PARTY_LICENSES/DeepAnalyze-MIT-LICENSE)
- [`THIRD_PARTY_LICENSES/StatABench-GPLv3-LICENSE`](THIRD_PARTY_LICENSES/StatABench-GPLv3-LICENSE)
