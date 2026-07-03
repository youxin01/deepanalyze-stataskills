# 医院运营与患者结局核心分析

你是一名医院数据分析顾问。院方给了几份运营和患者结局相关数据，希望你写一份中文 Markdown 分析报告，用来帮助管理层理解近期运营压力和患者结局风险。

请把它当成一个正常的院内分析任务，而不是工具演示。报告正文要围绕发现和建议展开。

## 数据文件

- `hospital_stay.csv`：住院时长、年龄、严重程度评分、是否手术。
- `er_arrivals.csv`：按小时记录的急诊患者到诊量。
- `whas500.csv`：心梗患者随访、生存状态和临床协变量；可用字段包括 `AGE`、`GENDER`、`HR`、`SYSBP`、`DIASBP`、`BMI`、`CVD`、`AFB`、`SHO`、`CHF`、`LOS`、`LENFOL`、`FSTAT`、`TECHNIQUE` 等。
- `chemo_data.csv`：治疗组和对照组的生存时间与结局；只有 `time`、`status`、`group` 三列。

## 分析要求

- 重要：不要分阶段先探索再继续。第一段 Python 代码必须一次性读取四个文件、完成全部统计分析、打印 `FACTS_FOR_REPORT`，并保存 `FACTS_FOR_REPORT.json`。后续报告只能基于这一次成功输出。
- 请优先用一个 Python 代码块完成主要计算，避免把任务拆成很多轮。每个代码块都要重新导入 `from stataskills import run_tool` 并读取需要的数据，因为不同代码块之间变量不一定保留。
- 读取并理解每个数据文件的字段、样本量和基础质量。
- 对 `hospital_stay.csv` 做描述统计、缺失值/异常值检查、相关性分析，并建立一个多变量住院时长模型。
- 对 `er_arrivals.csv` 做时间序列分析，判断是否平稳、是否存在周期结构，并给出排班含义。
- 对 `whas500.csv` 和 `chemo_data.csv` 做生存分析，包含 Kaplan-Meier、log-rank 或 Cox 模型中适合的方法。
- 如果某个方法因为数据不适合而失败，请在报告中说明原因，不要硬解释。
- 报告正文要像正常业务分析报告，不要把重点写成“工具展示”。
- 不能直接写报告。第一步必须输出并执行 `<Code>` 代码块，代码成功输出 `FACTS_FOR_REPORT` 后，第二步才能写最终报告。
- 每一个具体数值、p 值、HR、均值、比例和建议强度都必须来自你刚刚执行成功的 Python 输出；若未计算，不能写具体数值。
- 请在主要 Python 代码最后打印一个 `FACTS_FOR_REPORT` JSON，只放最终报告允许引用的事实。最终报告只能引用这个 JSON 或同一个代码块成功输出里的数值。
- 如果要写急诊高峰时段，请先在代码中按 `Hour_of_Day` 计算平均到诊量并打印。没有计算就不要写具体时段。
- 如果要写 `chemo_data.csv` 的组别中位生存时间，请先按 `group` 计算并打印。没有计算就只写 log-rank 检验结果。
- 如果要写 Kaplan-Meier 某个时间点的生存概率，请先计算并打印对应时间点；不要把输出中的前几个 timeline 点误写成固定年份生存概率。
- `test_stationarity` 输出 `stationary: True` 时应解释为统计检验支持平稳；不要写成非平稳。
- 本任务最终报告禁止写任何固定年份生存率、周末就诊量、占全天比例、未计算 HR 等没有由代码明确计算的结论。`logrank_test_compare` 不输出 HR，所以化疗部分不要写 HR。
- `kaplan_meier_plot` 在本任务中只用于说明已做分组生存曲线摘要；除非你额外明确计算指定时间点，否则最终报告不要写任何 TECHNIQUE 组的具体生存率。
- 不要使用数据中不存在的字段、诊断、治疗器械、药物分组或安全性概念；本任务只允许围绕已给字段做运营、生存时间和事件差异解释。
- 对 `whas500.csv` 的 `TECHNIQUE` 只能按数据中真实取值描述，不要把它改写成药物或支架治疗。
- 对 `chemo_data.csv` 只能讨论 `group`、`time`、`status` 对应的生存时间/事件差异，不能扩展到数据没有记录的其他临床终点。
- 不要写“待分析”“后续分析”“研究扩展”“处理后模型稳定性提高”这类没有被当前代码完成或验证的表达。
- 为了复现，请在报告最后增加一个简短的“附录：统计方法与函数调用记录”，列出每个主要结论对应的统计方法、输入数据、关键字段，以及实际调用的 `stataskills.run_tool("函数名", ...)` 函数名。

## 工具使用要求

当前执行环境已经安装 `stataskills`。涉及统计检验、回归、时间序列、生存分析时，请优先使用：

```python
from stataskills import run_tool, tool_help, list_tools
```

不要在有匹配 `stataskills` 工具时手写 scipy/statsmodels/lifelines/pmdarima/sklearn 的底层分析代码。图表和轻量 pandas 整理可以自行编写。
不要调用工具清单以外的函数名；如果不确定函数是否存在，先 `print(list_tools())` 或 `print(tool_help("函数名"))`。本任务不需要 `anova`、`normality_test`、`regression_diagnostics`、`variance_inflation_factor`、`residual_analysis` 这些函数名。

必须执行的代码如下：

```python
import json
from stataskills import run_tool

hospital = run_tool("read_csv", file="hospital_stay.csv")
er = run_tool("read_csv", file="er_arrivals.csv")
whas = run_tool("read_csv", file="whas500.csv")
chemo = run_tool("read_csv", file="chemo_data.csv")

hospital_desc = run_tool("describe", data=hospital, columns=["Length_of_Stay_days", "Patient_Age", "Severity_Score", "Is_Surgical"])
hospital_missing = run_tool("check_missing_values", data=hospital)
hospital_outliers = run_tool("detect_outliers", data=hospital, columns=["Length_of_Stay_days"])
hospital_corr = run_tool("correlation_analysis", data=hospital, method="pearson")
hospital_reg = run_tool("multivariable_linear_regression", data=hospital, y_col="Length_of_Stay_days", x_cols=["Patient_Age", "Severity_Score", "Is_Surgical"])

er_stationarity = run_tool("test_stationarity", data=er, column="Patient_Arrivals", method="adf")
er_stl = run_tool("decompose_stl", data=er, column="Patient_Arrivals", period=24)
er_hourly = er.groupby("Hour_of_Day")["Patient_Arrivals"].mean().round(3).to_dict()
er_peak_hour = max(er_hourly, key=er_hourly.get)
er_peak_value = er_hourly[er_peak_hour]

whas_km = run_tool("kaplan_meier_plot", data=whas, duration_col="LENFOL", event_col="FSTAT", group_col="TECHNIQUE")
whas_cox = run_tool("fit_cox_model", data=whas, duration_col="LENFOL", event_col="FSTAT", covariates=["AGE", "BMI", "HR"])

chemo_logrank = run_tool("logrank_test_compare", data=chemo, duration_col="time", event_col="status", group_col="group")
chemo_median_time = chemo.groupby("group")["time"].median().round(3).to_dict()
chemo_event_rate = chemo.groupby("group")["status"].mean().round(3).to_dict()

facts = {
    "hospital_shape": list(hospital.shape),
    "hospital_desc": hospital_desc,
    "hospital_missing": hospital_missing,
    "hospital_outliers": hospital_outliers,
    "hospital_regression": hospital_reg,
    "er_stationarity": er_stationarity,
    "er_stl": er_stl,
    "er_peak_hour": er_peak_hour,
    "er_peak_value": er_peak_value,
    "whas_shape": list(whas.shape),
    "whas_km_groups": list(whas_km.keys()),
    "whas_cox": whas_cox,
    "chemo_shape": list(chemo.shape),
    "chemo_logrank": chemo_logrank,
    "chemo_median_time": chemo_median_time,
    "chemo_event_rate": chemo_event_rate,
}

print("FACTS_FOR_REPORT")
print(json.dumps(facts, ensure_ascii=False, indent=2))
with open("FACTS_FOR_REPORT.json", "w", encoding="utf-8") as f:
    json.dump(facts, f, ensure_ascii=False, indent=2)
```

代码执行成功后，报告请使用中文，给出关键数值结果和谨慎解释。最终回答只输出报告正文，不要在报告前后输出额外分析过程。必须覆盖这些工具函数：`read_csv`、`describe`、`check_missing_values`、`detect_outliers`、`correlation_analysis`、`multivariable_linear_regression`、`test_stationarity`、`decompose_stl`、`kaplan_meier_plot`、`logrank_test_compare`、`fit_cox_model`。

最终报告请使用以下结构，并在附录里写出完整 `stataskills.run_tool("...")` 函数名：

```markdown
# 医院运营与患者结局核心分析报告

## 摘要

## 一、住院时长与运营压力

## 二、急诊到诊时间模式

## 三、心梗患者随访风险

## 四、治疗组生存时间比较

## 五、管理建议

## 附录：统计方法与函数调用记录
| 结论位置 | 数据 | 关键字段 | stataskills 函数 |
|---|---|---|---|
```
