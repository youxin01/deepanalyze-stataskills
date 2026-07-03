# 产品增长与转化实验分析

你是一名产品增长数据分析师。增长团队希望评估一次 A/B 实验是否改善用户转化和参与度，并理解不同用户行为指标与转化、订阅之间的关系。

请把它当成一个正常的产品分析任务，而不是工具演示。最终报告需要围绕“实验是否值得继续扩大、还有哪些风险、下一轮实验如何设计”展开。

## 数据文件

- `conversion_data.csv`：A/B 实验分组、用户游戏时长、年龄和是否转化。
- `website_session_data.csv`：用户会话、订阅、设备、地区、游戏次数、参与度等字段。
- `advertising_click.csv`：广告点击、用户年龄、站点停留时长、收入、互联网使用量等字段。

## 分析要求

- 先用 Python 代码完成主要计算，然后基于成功输出写中文 Markdown 报告。
- 统计分析优先调用 `stataskills.run_tool(...)`，不要在已有匹配工具时手写底层 scipy/statsmodels/sklearn 代码。
- 只能调用下面这些 `stataskills` 工具名：`read_csv`、`describe`、`check_missing_values`、`detect_outliers`、`correlation_analysis`、`contingency_test`、`ab_ttest`、`bootstrap_abtest`、`ab_power_analysis`。
- 不要调用 `interaction_analysis`、`logistic_regression`、`nonlinear_analysis`、`anova`、`regression_diagnostics` 或其他不在上面清单中的工具名。
- 请优先只写并执行一个完整 Python 代码块；如果代码失败，重新执行时必须从读取三个数据文件开始，不要依赖上一个代码块中的变量。
- 不能直接写报告。第一步必须输出并执行 `<Code>` 代码块，代码成功输出 `FACTS_FOR_REPORT` 后，第二步才能写最终报告。
- 至少覆盖数据质量、描述统计、A/B 连续指标差异、转化/订阅类分类变量关系、bootstrap 置信区间和下一轮样本量估计。
- 每个具体数值、p 值、置信区间和建议必须来自代码输出；没有计算就不要写。
- 不要把相关性或组间差异写成因果结论。可以写“相关”“差异”“实验组表现”，但不要写“导致”“证明提升”。
- 最终报告必须是中文，不要输出英文报告。
- 最终报告最后必须有“附录：统计方法与函数调用记录”，列出关键结论对应的数据、字段和实际调用的 `stataskills.run_tool("函数名", ...)`。

## 必须执行的代码

```python
import json
from stataskills import run_tool

conversion = run_tool("read_csv", file="conversion_data.csv")
sessions = run_tool("read_csv", file="website_session_data.csv")
ads = run_tool("read_csv", file="advertising_click.csv")

conversion_desc = run_tool("describe", data=conversion)
session_desc = run_tool("describe", data=sessions, columns=["play_game_seconds", "games_played", "session_time_seconds", "engagement_score"])
ads_desc = run_tool("describe", data=ads, columns=["Daily Time Spent on Site", "Age", "Area Income", "Daily Internet Usage", "Clicked on Ad"])

conversion_missing = run_tool("check_missing_values", data=conversion)
session_missing = run_tool("check_missing_values", data=sessions)
ads_missing = run_tool("check_missing_values", data=ads)

conversion_outliers = run_tool("detect_outliers", data=conversion, columns=["play_game_seconds", "user_age"])
session_outliers = run_tool("detect_outliers", data=sessions, columns=["play_game_seconds", "session_time_seconds", "engagement_score"])

group_conversion = conversion.groupby("group")["converted"].agg(["count", "mean"]).round(4).to_dict()
session_by_group = sessions.groupby("group")[["play_game_seconds", "session_time_seconds", "engagement_score"]].mean().round(3).to_dict()

conversion_chi = run_tool("contingency_test", data=conversion, columns=["group", "converted"], method="chi-square independence")
session_ttest = run_tool("ab_ttest", data=sessions, group_col="group", value_col="engagement_score", group_A="A", group_B="B")
session_bootstrap = run_tool("bootstrap_abtest", data=sessions, group_col="group", value_col="engagement_score", group_A="A", group_B="B")
power = run_tool("ab_power_analysis", test_type="proportion", baseline=float(conversion[conversion["group"] == "A"]["converted"].mean()), effect=0.02)

ads_corr = run_tool("correlation_analysis", data=ads[["Daily Time Spent on Site", "Age", "Area Income", "Daily Internet Usage", "Clicked on Ad"]], method="pearson")

facts = {
    "conversion_shape": list(conversion.shape),
    "session_shape": list(sessions.shape),
    "ads_shape": list(ads.shape),
    "conversion_desc": conversion_desc,
    "session_desc": session_desc,
    "ads_desc": ads_desc,
    "conversion_missing": conversion_missing,
    "session_missing": session_missing,
    "ads_missing": ads_missing,
    "conversion_outliers": conversion_outliers,
    "session_outliers": session_outliers,
    "group_conversion": group_conversion,
    "session_by_group": session_by_group,
    "conversion_chi": conversion_chi,
    "session_ttest": session_ttest,
    "session_bootstrap": session_bootstrap,
    "power": power,
    "ads_corr": ads_corr,
}

print("FACTS_FOR_REPORT")
print(json.dumps(facts, ensure_ascii=False, indent=2))
with open("FACTS_FOR_REPORT.json", "w", encoding="utf-8") as f:
    json.dump(facts, f, ensure_ascii=False, indent=2)
```

## 报告结构

代码执行成功后，请只输出最终报告正文，不要输出额外解释。建议使用：

```markdown
# 产品增长与转化实验分析报告

## 摘要

## 一、实验数据质量与样本概况

## 二、转化率与用户参与度差异

## 三、广告点击与用户行为关系

## 四、下一轮实验建议

## 附录：统计方法与函数调用记录
```
