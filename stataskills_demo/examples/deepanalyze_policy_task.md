# 政策效果与因果评估分析

你是一名政策评估数据分析师。研究团队希望评估不同政策或项目干预是否对事故数量、就业收入和宏观经济指标产生影响，并判断结论是否足够稳健。

请把它当成一个正常的政策评估任务，而不是工具演示。最终报告需要帮助决策者理解“是否有政策效果、证据强不强、还需要什么补充验证”。

## 数据文件

- `accidents_did.csv`：事故数量的处理组/对照组面板数据。
- `placebo_did.csv`：用于安慰剂时间点检查的 DID 数据。
- `lalonde_data.csv`：就业培训项目数据，包含处理组、协变量和后续收入。
- `synthetic_gdp_reform.csv`：国家层面的 GDP 改革政策合成控制数据。

## 分析要求

- 先用 Python 代码完成主要计算，然后基于成功输出写中文 Markdown 报告。
- 统计分析优先调用 `stataskills.run_tool(...)`，不要在已有匹配工具时手写底层 statsmodels/sklearn/cvxpy 代码。
- 不能直接写报告。第一步必须输出并执行 `<Code>` 代码块，代码成功输出 `FACTS_FOR_REPORT` 后，第二步才能写最终报告。
- 至少覆盖数据质量、描述统计、DID、placebo DID、PSM ATT、synthetic control。
- 每个具体数值、p 值、ATT、DID 系数、合成控制差异和建议必须来自代码输出；没有计算就不要写。
- 必须区分 DID、PSM、synthetic control 的解释边界。不要把相关性或匹配后的差异写成随机实验因果结论。
- 不要把 placebo 结果解释成真实政策效果。
- 最终报告最后必须有“附录：统计方法与函数调用记录”，列出关键结论对应的数据、字段和实际调用的 `stataskills.run_tool("函数名", ...)`。

## 必须执行的代码

```python
import json
from stataskills import run_tool

accidents = run_tool("read_csv", file="accidents_did.csv")
placebo = run_tool("read_csv", file="placebo_did.csv")
lalonde = run_tool("read_csv", file="lalonde_data.csv")
gdp = run_tool("read_csv", file="synthetic_gdp_reform.csv")

accidents_desc = run_tool("describe", data=accidents)
placebo_desc = run_tool("describe", data=placebo)
lalonde_desc = run_tool("describe", data=lalonde, columns=["treat", "age", "educ", "re74", "re75", "re78"])
gdp_desc = run_tool("describe", data=gdp, columns=["year", "GDP"])

accidents_missing = run_tool("check_missing_values", data=accidents)
placebo_missing = run_tool("check_missing_values", data=placebo)
lalonde_missing = run_tool("check_missing_values", data=lalonde)
gdp_missing = run_tool("check_missing_values", data=gdp)

accidents_did = run_tool("estimate_did_effect", data=accidents, outcome="accidents", treat_col="treat", time_col="year", post_year=2020)
placebo_did = run_tool("estimate_did_effect", data=placebo, outcome="outcome", treat_col="treat_group", time_col="year", post_year=2020, placebo_year=2019)

psm_att = run_tool(
    "estimate_ATT_with_psm",
    data=lalonde,
    treatment="treat",
    outcome="re78",
    covariates=["age", "educ", "black", "hispan", "married", "nodegree", "re74", "re75"],
)

synth = run_tool(
    "synthetic_control",
    df=gdp,
    time_col="year",
    unit_col="country",
    outcome_col="GDP",
    treated_unit="Country_X",
    intervention_time=1995,
)

facts = {
    "accidents_shape": list(accidents.shape),
    "placebo_shape": list(placebo.shape),
    "lalonde_shape": list(lalonde.shape),
    "gdp_shape": list(gdp.shape),
    "accidents_desc": accidents_desc,
    "placebo_desc": placebo_desc,
    "lalonde_desc": lalonde_desc,
    "gdp_desc": gdp_desc,
    "accidents_missing": accidents_missing,
    "placebo_missing": placebo_missing,
    "lalonde_missing": lalonde_missing,
    "gdp_missing": gdp_missing,
    "accidents_did": accidents_did,
    "placebo_did": placebo_did,
    "psm_att": psm_att,
    "synthetic_control": synth,
}

print("FACTS_FOR_REPORT")
print(json.dumps(facts, ensure_ascii=False, indent=2))
with open("FACTS_FOR_REPORT.json", "w", encoding="utf-8") as f:
    json.dump(facts, f, ensure_ascii=False, indent=2)
```

## 报告结构

代码执行成功后，请只输出最终报告正文，不要输出额外解释。建议使用：

```markdown
# 政策效果与因果评估分析报告

## 摘要

## 一、数据质量与研究设计

## 二、事故政策的 DID 估计

## 三、就业培训项目的 PSM 估计

## 四、GDP 改革的合成控制评估

## 五、稳健性与决策建议

## 附录：统计方法与函数调用记录
```
