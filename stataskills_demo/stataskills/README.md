# stataskills

`stataskills` packages the statistical functions from StatABench as a normal
Python library for code-execution agents such as DeepAnalyze. It avoids MCP
server/client plumbing: generated Python code can import the package directly
inside the execution environment.

## Agent-facing API

Use `run_tool()` as the stable interface:

```python
from stataskills import run_tool, list_tools, tool_help

print(list_tools())
print(tool_help("linear_regression"))

df = run_tool("read_csv", file="Simpson.csv")
summary = run_tool("describe", data=df, columns=["income", "success"])
fit = run_tool("linear_regression", data=df, x="income", y="success")
```

`run_tool()` returns JSON-safe Python values for reports and logs. The only
exception is `read_csv`, which returns a pandas `DataFrame` so later tool calls
can reuse it.

## Input Rules

Most statistical tools accept either:

- `data="path/to/file.csv"`
- `data=df` where `df` is a pandas `DataFrame`

Convenience aliases are supported for common model-generated argument names:

- `file=...` is normalized to `data=...`
- `columns=["x"]` is normalized to `column="x"` for single-column statistics
- `statistic="mean"` is normalized to `method="mean"`
- `x="col"` and `y="col"` are normalized to regression arguments where needed
- `linear_regression` is an alias for `simple_linear_regression`

For exact signatures, call:

```python
from stataskills import tool_help
print(tool_help("tool_name"))
```

## Direct Function API

Direct imports are also available when deterministic code is preferred:

```python
from stataskills import read_csv, describe, simple_linear_regression

df = read_csv(file="Simpson.csv")
print(describe(data=df, columns=["income"]))
print(simple_linear_regression(df, x_col="income", y_col="success"))
```

## DeepAnalyze Integration

DeepAnalyze has been configured to append a toolkit instruction to each user
request. During code generation, the model is told to prefer:

```python
from stataskills import run_tool, list_tools, tool_help
```

for EDA, missingness/outlier checks, hypothesis tests, correlation, regression,
time series, survival analysis, A/B testing, Bayesian inference, causal
inference, and multiple-testing correction.
