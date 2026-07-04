# DeepAnalyze 接入 StatABench 统计工具库说明

这份文档说明本次为了让 DeepAnalyze 能使用 StatABench 里的统计函数，具体改了哪些文件、接入方式是什么、怎么验证，以及现在推荐用哪个示例报告做展示。

## 1. 接入方式

这次没有走 MCP server/client，而是把 StatABench 的统计函数整理成普通 Python 包：`stataskills`。

DeepAnalyze 的代码执行环境里已经安装这个包，所以模型生成 Python 代码时可以直接调用：

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

这个方案的兼容点很简单：

- DeepAnalyze 仍然按原流程上传文件、创建 workspace、让模型生成 Python 代码。
- Python 执行环境中已经能 `import stataskills`。
- DeepAnalyze 的 prompt 注入里告诉模型：统计分析优先用 `stataskills.run_tool(...)`，不要随便手写底层 scipy/statsmodels/lifelines 代码，也不要编造不存在的工具名。

## 2. StatABench 侧改动

### 2.1 新增 `stataskills` 包

新增目录：

```text
/nfsdata/zyx/statabench/StatABench/stataskills/
```

主要文件：

```text
stataskills/__init__.py
stataskills/tools.py
stataskills/README.md
```

其中：

- `tools.py`：整理原 MCP server 中的统计函数。
- `__init__.py`：提供 agent/DeepAnalyze 更稳定的统一入口。
- `README.md`：说明普通 Python 包方式怎么使用。

主要公开 API：

```python
from stataskills import run_tool, list_tools, tool_help
```

`run_tool()` 支持常见兼容写法，例如：

- `read_csv` / `load_csv`
- `linear_regression` -> `simple_linear_regression`
- `missing_values` -> `check_missing_values`
- `outliers` -> `detect_outliers`
- `correlation` -> `correlation_analysis`
- `file=...` 自动转成 `data=...`
- `x/y`、`target/predictors`、`covariates` 等常见参数名自动归一到真实函数签名

### 2.2 新增安装配置

新增：

```text
/nfsdata/zyx/statabench/StatABench/pyproject.toml
```

用于把 StatABench 安装成普通 Python 包：

```bash
conda run -n deepanalyze_app pip install -e '/nfsdata/zyx/statabench/StatABench[full]'
```

`[full]` 包含时间序列、生存分析、贝叶斯、因果推断等依赖。

### 2.3 兼容性修复

全函数验证时修复了几个真实调用问题：

- `ks_test` 的 one-sample 分支兼容当前 SciPy。
- `ab_power_analysis` 将 numpy-like solver 输出转成标量后再 `ceil`。
- `check_missing_values(columns=None)` 默认检查全部列。
- `detect_outliers(columns=None)` 默认检查全部数值列。

这些修改没有删除原函数，也没有改变基础能力，只是让 agent 生成代码时更不容易因为参数遗漏或库版本差异失败。

## 3. DeepAnalyze 侧改动

DeepAnalyze 只改了一个核心文件：

```text
/nfsdata/zyx/statabench/skills-create/DeepAnalyze/API/utils.py
```

改动内容：

- 新增 `STATASKILLS_PROMPT`。
- 在 `prepare_vllm_messages()` 中把 `STATASKILLS_PROMPT` 追加到用户任务后面。

这个 prompt 会告诉模型：

- 当前 Python 环境已安装 `stataskills`。
- 统计分析优先使用 `from stataskills import run_tool, list_tools, tool_help`。
- 不确定工具签名时用 `tool_help()` 或 `list_tools()`。
- 不要编造不存在的工具名。
- 最终报告里的数值、p 值、HR、百分比和建议必须能追溯到成功执行的代码输出。

因此 DeepAnalyze 框架本身没有新增工具协议，也没有新增 MCP client。它只是通过“执行环境可 import + prompt 注入”兼容 `stataskills`。

## 4. 工程验证：全部公开函数可调用

新增脚本：

```text
/nfsdata/zyx/statabench/StatABench/scripts/verify_stataskills_all_tools.py
```

运行：

```bash
/data1/zyx/conda/envs/deepanalyze_app/bin/python \
  /nfsdata/zyx/statabench/StatABench/scripts/verify_stataskills_all_tools.py
```

当前结果：

```text
Total cases: 55
Passed: 55
Failed: 0
Public tools covered by primary PASS: 38 / 38
```

产物：

```text
/nfsdata/zyx/statabench/StatABench/artifacts/stataskills_call_matrix.md
/nfsdata/zyx/statabench/StatABench/artifacts/stataskills_call_matrix.json
```

这个矩阵是工程验收用的，证明每个公开工具至少有一个主路径可以正常调用。

## 5. 三个自然展示任务

为了方便展示 DeepAnalyze 作为正常分析框架调用 `stataskills`，现在保留三个自然任务，而不是只做函数覆盖清单：

```text
/nfsdata/zyx/statabench/StatABench/examples/deepanalyze_hospital_task.md
/nfsdata/zyx/statabench/StatABench/examples/deepanalyze_growth_task.md
/nfsdata/zyx/statabench/StatABench/examples/deepanalyze_policy_task.md
/nfsdata/zyx/statabench/StatABench/examples/run_deepanalyze_demo_tasks.py
```

这三个例子分别是：

- `hospital`：医院运营分析，问题只问住院时间影响因素和急诊时段压力。
- `growth`：产品增长与转化实验，问题只问 B 组是否值得继续放量。
- `policy`：政策效果评估，问题只问政策实施后事故数量是否有明显变化。

统一 runner 的原则是：

- 只保存 DeepAnalyze 原始输出。
- 不做二次模型调用。
- 不生成 `verified_report`。
- 不润色、不改写最终报告正文。
- 只把 `<Answer>...</Answer>` 正文原样抽取成短文件名，方便查找。

这三个 prompt 都刻意保持成真实用户会问的问题，不再放工具清单、必需代码块或长篇格式要求。runner 的验证标准也相应改成：原始输出里至少出现一次合法 `stataskills.run_tool(...)` 调用、最终报告非空、没有明显禁用内容。核心统计工具未命中或模型尝试了不存在的工具名会保留为 warning，不再直接判失败。

运行全部三个任务：

```bash
/data1/zyx/conda/envs/deepanalyze_app/bin/python \
  /nfsdata/zyx/statabench/StatABench/examples/run_deepanalyze_demo_tasks.py --task all
```

也可以单独运行任意一个：

```bash
/data1/zyx/conda/envs/deepanalyze_app/bin/python \
  /nfsdata/zyx/statabench/StatABench/examples/run_deepanalyze_demo_tasks.py --task growth
```

短文件名输出位置：

```text
/nfsdata/zyx/statabench/StatABench/artifacts/reports/hospital.md
/nfsdata/zyx/statabench/StatABench/artifacts/reports/growth.md
/nfsdata/zyx/statabench/StatABench/artifacts/reports/policy.md
```

对应原始 assistant 内容、API 响应和验证文件：

```text
/nfsdata/zyx/statabench/StatABench/artifacts/reports/hospital_raw.md
/nfsdata/zyx/statabench/StatABench/artifacts/reports/hospital_response.json
/nfsdata/zyx/statabench/StatABench/artifacts/reports/hospital_validation.json
/nfsdata/zyx/statabench/StatABench/artifacts/reports/growth_raw.md
/nfsdata/zyx/statabench/StatABench/artifacts/reports/growth_response.json
/nfsdata/zyx/statabench/StatABench/artifacts/reports/growth_validation.json
/nfsdata/zyx/statabench/StatABench/artifacts/reports/policy_raw.md
/nfsdata/zyx/statabench/StatABench/artifacts/reports/policy_response.json
/nfsdata/zyx/statabench/StatABench/artifacts/reports/policy_validation.json
```

当前三份验证文件均为 `passed: true`。验证器检查的是原始输出里是否真的出现了 `run_tool(...)` 调用、最终报告是否为空、是否出现明显禁用内容；未知工具名和核心工具未命中会记录为 warning，用来保留模型原始试错过程。

## 6. 推荐怎么看结果

如果你要展示“最终报告长什么样”，优先看这三个短文件：

```text
/nfsdata/zyx/statabench/StatABench/artifacts/reports/hospital.md
/nfsdata/zyx/statabench/StatABench/artifacts/reports/growth.md
/nfsdata/zyx/statabench/StatABench/artifacts/reports/policy.md
```

如果你要展示“DeepAnalyze 确实调用了我们的统计工具”，看对应的 raw 文件，例如：

```text
/nfsdata/zyx/statabench/StatABench/artifacts/reports/hospital_raw.md
```

里面能看到 DeepAnalyze 生成并执行的代码，例如：

```text
from stataskills import run_tool
run_tool("read_csv", ...)
run_tool("multivariable_linear_regression", ...)
run_tool("test_stationarity", ...)
run_tool("fit_cox_model", ...)
```

如果你要看机器验收结果，看：

```text
/nfsdata/zyx/statabench/StatABench/artifacts/reports/hospital_validation.json
/nfsdata/zyx/statabench/StatABench/artifacts/reports/growth_validation.json
/nfsdata/zyx/statabench/StatABench/artifacts/reports/policy_validation.json
```

DeepAnalyze 自己生成的附件会下载到：

```text
/nfsdata/zyx/statabench/StatABench/artifacts/reports/generated/<task>/
```

## 7. 常用命令

检查服务：

```bash
curl http://localhost:8200/health
curl http://localhost:8000/v1/models
```

重新跑全函数验证：

```bash
/data1/zyx/conda/envs/deepanalyze_app/bin/python \
  /nfsdata/zyx/statabench/StatABench/scripts/verify_stataskills_all_tools.py
```

重新跑三个自然报告：

```bash
/data1/zyx/conda/envs/deepanalyze_app/bin/python \
  /nfsdata/zyx/statabench/StatABench/examples/run_deepanalyze_demo_tasks.py --task all
```

只重跑某一个报告：

```bash
/data1/zyx/conda/envs/deepanalyze_app/bin/python \
  /nfsdata/zyx/statabench/StatABench/examples/run_deepanalyze_demo_tasks.py --task policy
```

## 8. 旧脚本和旧 showcase

旧的 showcase 文件仍然保留：

```text
/nfsdata/zyx/statabench/StatABench/examples/deepanalyze_showcase_task.md
/nfsdata/zyx/statabench/StatABench/examples/deepanalyze_showcase_driver.py
/nfsdata/zyx/statabench/StatABench/examples/run_deepanalyze_showcase_report.py
```

旧的医院专用 runner 已从 release 包中移除。这个脚本会基于抽取出的 facts 再发起报告改写请求，容易让人误解展示报告不是原始模型输出。

这些旧 showcase 更像工程调试或早期单任务实验，不建议作为主要展示报告。主要展示建议使用统一 runner 产出的三个短文件名原始报告。
