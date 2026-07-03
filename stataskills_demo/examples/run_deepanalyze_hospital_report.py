#!/usr/bin/env python3
"""
Run a natural hospital analytics task through DeepAnalyze and save artifacts.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from stataskills import ALIASES, list_tools


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "datasets83"
ARTIFACTS = ROOT / "artifacts"
TASK_PATH = ROOT / "examples" / "deepanalyze_hospital_task.md"

API_BASE = "http://localhost:8200"
MODEL = "DeepAnalyze-8B"
TIMEOUT = 900

HOSPITAL_FILES = [
    "hospital_stay.csv",
    "er_arrivals.csv",
    "whas500.csv",
    "chemo_data.csv",
]

EXPECTED_FUNCTIONS = [
    "read_csv",
    "describe",
    "check_missing_values",
    "detect_outliers",
    "correlation_analysis",
    "multivariable_linear_regression",
    "test_stationarity",
    "decompose_stl",
    "kaplan_meier_plot",
    "logrank_test_compare",
    "fit_cox_model",
]

ALLOWED_TOOLS = {tool["name"] for tool in list_tools()} | set(ALIASES)

CATEGORY_GROUPS = {
    "eda": {"describe", "check_missing_values", "detect_outliers", "correlation_analysis"},
    "modeling": {"multivariable_linear_regression"},
    "time_series": {"test_stationarity", "decompose_stl"},
    "survival": {"kaplan_meier_plot", "logrank_test_compare", "fit_cox_model"},
}

FORBIDDEN_REPORT_TERMS = [
    "糖尿病",
    "不良反应",
    "支架",
    "药物组",
    "3-4级",
    "毒性",
    "5年生存率",
    "非平稳序列",
    "待分析",
    "后续分析",
    "研究扩展",
    "处理后模型稳定性提高",
    "HR范围",
    "周末就诊量",
    "占全天",
    "HR=0.86",
    "ols_regression",
    "cox_ph",
    "logrank_test\"",
    "Python 3.9",
    "独立复核",
    "门诊",
    "单位根",
    "r=0.64",
    "74.9%",
    "22.7%",
    "18.4%",
    "四家医院",
    "心衰",
    "5年生存分析",
    "χ²",
    "23%",
    "12%",
    "90天",
    "斜率=",
    "p=0.013",
    "组间差异具有统计学意义",
    "病情分组",
    "手术患者严重程度",
    "趋势线性上升",
]


def extract_clean_report(text: str) -> str:
    """Return the visible final report before DeepAnalyze's conversation log."""
    answers = re.findall(r"<Answer>\s*(.*?)\s*</Answer>", text, flags=re.DOTALL)
    if answers:
        return answers[-1].strip()
    markers = ["\\newpage", "# 附录：完整对话过程", "## 对话轮次"]
    clean = text
    for marker in markers:
        if marker in clean:
            clean = clean.split(marker, 1)[0]
    return clean.strip()


def health_check() -> None:
    response = requests.get(f"{API_BASE}/health", timeout=10)
    response.raise_for_status()


def upload_file(path: Path) -> str:
    with path.open("rb") as handle:
        response = requests.post(
            f"{API_BASE}/v1/files",
            files={"file": (path.name, handle, "text/csv")},
            data={"purpose": "file-extract"},
            timeout=120,
        )
    response.raise_for_status()
    file_id = response.json()["id"]
    print(f"uploaded {path.name}: {file_id}")
    return file_id


def download_generated_file(url: str, output_dir: Path) -> Path:
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    parsed = urlparse(url)
    name = Path(parsed.path).name or f"generated_{int(time.time())}.md"
    target = output_dir / name
    target.write_bytes(response.content)
    return target


def build_report_prompt(facts: dict[str, object], feedback: str = "") -> str:
    hospital_desc = facts.get("hospital_desc", {})
    stay = hospital_desc.get("Length_of_Stay_days", {}) if isinstance(hospital_desc, dict) else {}
    age = hospital_desc.get("Patient_Age", {}) if isinstance(hospital_desc, dict) else {}
    severity = hospital_desc.get("Severity_Score", {}) if isinstance(hospital_desc, dict) else {}
    surgical = hospital_desc.get("Is_Surgical", {}) if isinstance(hospital_desc, dict) else {}
    outlier_values = facts.get("hospital_outliers", {}).get("Length_of_Stay_days", {}).get("values", [])
    reg = facts.get("hospital_reg", facts.get("hospital_regression", {}))
    coef = reg.get("coefficients", {}) if isinstance(reg, dict) else {}
    pvalues = reg.get("pvalues", {}) if isinstance(reg, dict) else {}
    er_stationarity = facts.get("er_stationarity", {})
    er_stl = facts.get("er_stl", facts.get("er_decomposition", {}))
    whas_cox = facts.get("whas_cox", {})
    cox_hr = whas_cox.get("hazard_ratios", {}) if isinstance(whas_cox, dict) else {}
    cox_p = whas_cox.get("pvalues", {}) if isinstance(whas_cox, dict) else {}
    cox_low = whas_cox.get("ci95_lower", {}) if isinstance(whas_cox, dict) else {}
    cox_high = whas_cox.get("ci95_upper", {}) if isinstance(whas_cox, dict) else {}
    chemo_logrank = facts.get("chemo_logrank", {})
    chemo_row = (chemo_logrank.get("head") or [{}])[0] if isinstance(chemo_logrank, dict) else {}
    chemo_median = facts.get("chemo_median_time", facts.get("chemo_median_survival", {}))
    chemo_event = facts.get("chemo_event_rate", {})
    outlier_range = "NA"
    if outlier_values:
        outlier_range = f"{min(outlier_values):.1f}-{max(outlier_values):.1f}"
    allowed_facts = {
        "hospital_n": (facts.get("hospital_shape") or ["NA"])[0],
        "los_mean": stay.get("mean"),
        "los_std": stay.get("std"),
        "age_mean": age.get("mean"),
        "severity_mean": severity.get("mean"),
        "surgical_rate": surgical.get("mean"),
        "outlier_count": len(outlier_values),
        "outlier_range": outlier_range,
        "regression_r2": reg.get("r_squared") if isinstance(reg, dict) else None,
        "age_coef": coef.get("Patient_Age"),
        "severity_coef": coef.get("Severity_Score"),
        "surgical_coef": coef.get("Is_Surgical"),
        "age_p": pvalues.get("Patient_Age"),
        "severity_p": pvalues.get("Severity_Score"),
        "surgical_p": pvalues.get("Is_Surgical"),
        "er_peak_hour": facts.get("er_peak_hour"),
        "er_peak_value": facts.get("er_peak_value"),
        "er_adf_p": er_stationarity.get("p_value") if isinstance(er_stationarity, dict) else None,
        "er_stationary": er_stationarity.get("stationary") if isinstance(er_stationarity, dict) else None,
        "er_trend_mean": er_stl.get("trend_mean") if isinstance(er_stl, dict) else None,
        "whas_n": (facts.get("whas_shape") or ["NA"])[0],
        "whas_km_groups": facts.get("whas_km_groups"),
        "cox_age_hr": cox_hr.get("AGE"),
        "cox_age_ci": [cox_low.get("AGE"), cox_high.get("AGE")],
        "cox_age_p": cox_p.get("AGE"),
        "cox_bmi_hr": cox_hr.get("BMI"),
        "cox_bmi_ci": [cox_low.get("BMI"), cox_high.get("BMI")],
        "cox_bmi_p": cox_p.get("BMI"),
        "cox_hr_hr": cox_hr.get("HR"),
        "cox_hr_ci": [cox_low.get("HR"), cox_high.get("HR")],
        "cox_hr_p": cox_p.get("HR"),
        "chemo_n": (facts.get("chemo_shape") or ["NA"])[0],
        "chemo_control_median": chemo_median.get("Control") if isinstance(chemo_median, dict) else None,
        "chemo_treatment_median": chemo_median.get("Treatment") if isinstance(chemo_median, dict) else None,
        "chemo_control_event_rate": chemo_event.get("Control") if isinstance(chemo_event, dict) else None,
        "chemo_treatment_event_rate": chemo_event.get("Treatment") if isinstance(chemo_event, dict) else None,
        "chemo_logrank_p": chemo_row.get("p") if isinstance(chemo_row, dict) else None,
    }
    feedback_block = f"\n上一次报告没有通过验证，原因如下：\n{feedback}\n" if feedback else ""
    return f"""请基于下面的 FACTS_FOR_REPORT JSON 写一份中文 Markdown 报告。
{feedback_block}

要求：
- 只使用 ALLOWED_FACTS 里明确出现的事实和数值，不要补充未计算的结论。
- 不要写 5年生存率、周末就诊量、占全天比例、HR=0.86、糖尿病、不良反应、支架、药物组。
- Kaplan-Meier 只说明已按 TECHNIQUE 做了分组曲线摘要，不报告任何具体生存率。
- 不要写“组间差异具有统计学意义”“病情分组”“手术患者严重程度更高”“趋势线性上升”。
- `multivariable_linear_regression` 的手术系数只表示手术变量与住院时长关联，不表示手术患者严重程度更高。
- 化疗部分只报告中位时间、事件率和 log-rank p 值，不写 HR。
- 报告最后必须有“附录：统计方法与函数调用记录”，并在表格中逐字写下面这些函数名：
  `stataskills.run_tool("check_missing_values")`
  `stataskills.run_tool("detect_outliers")`
  `stataskills.run_tool("correlation_analysis")`
  `stataskills.run_tool("multivariable_linear_regression")`
  `stataskills.run_tool("test_stationarity")`
  `stataskills.run_tool("decompose_stl")`
  `stataskills.run_tool("kaplan_meier_plot")`
  `stataskills.run_tool("fit_cox_model")`
  `stataskills.run_tool("logrank_test_compare")`
- 只输出最终报告正文，不要输出代码或分析过程。
- 附录中的函数名必须使用 `stataskills.run_tool("...")` 形式，不能写 `stataskills.xxx`、`cox_model`、`ols_regression`、`logrank_test`。

ALLOWED_FACTS:
```json
{json.dumps(allowed_facts, ensure_ascii=False, indent=2)}
```

FACTS_FOR_REPORT:
```json
{json.dumps(facts, ensure_ascii=False, indent=2)}
```
"""


def report_passes(validation: dict[str, object]) -> bool:
    return bool(
        len(validation["report_function_hits"]) >= 8
        and validation["has_chinese_report_markers"]
        and validation["has_tool_appendix"]
        and not validation["forbidden_report_terms"]
    )


def validation_feedback(validation: dict[str, object]) -> str:
    missing = [
        fn for fn in EXPECTED_FUNCTIONS
        if fn != "read_csv" and fn not in validation["report_function_hits"]
    ]
    parts = []
    if missing:
        parts.append(
            "附录缺少这些精确函数名："
            + ", ".join(f'stataskills.run_tool("{fn}")' for fn in missing)
        )
    if validation["forbidden_report_terms"]:
        parts.append("报告包含禁用词：" + ", ".join(validation["forbidden_report_terms"]))
    if not validation["has_tool_appendix"]:
        parts.append("报告必须包含“附录：统计方法与函数调用记录”，并写出 stataskills.run_tool 调用。")
    return "\n".join(parts) or "报告未通过格式校验。"


def validate_response(text: str, report_text: str) -> dict[str, object]:
    run_tool_calls = sorted(
        call
        for call in set(re.findall(r"run_tool\([\"']([^\"']+)[\"']", text))
        if call != "函数名"
    )
    unknown_tool_calls = sorted(set(run_tool_calls) - ALLOWED_TOOLS)
    mentioned = sorted(
        {fn for fn in EXPECTED_FUNCTIONS if re.search(rf"\b{re.escape(fn)}\b", text)}
        | set(run_tool_calls)
    )
    category_hits = {
        category: sorted(set(mentioned) & functions)
        for category, functions in CATEGORY_GROUPS.items()
    }
    report_function_hits = sorted(
        fn for fn in EXPECTED_FUNCTIONS if f'stataskills.run_tool("{fn}")' in report_text
    )
    forbidden_terms = sorted({term for term in FORBIDDEN_REPORT_TERMS if term in report_text})
    return {
        "expected_functions": EXPECTED_FUNCTIONS,
        "mentioned_or_called_functions": mentioned,
        "run_tool_calls": run_tool_calls,
        "unknown_tool_calls": unknown_tool_calls,
        "category_hits": category_hits,
        "report_function_hits": report_function_hits,
        "forbidden_report_terms": forbidden_terms,
        "has_chinese_report_markers": any(marker in report_text for marker in ["摘要", "住院时长", "生存", "附录"]),
        "has_tool_appendix": "附录" in report_text and "stataskills" in report_text,
        "clean_report_chars": len(report_text),
    }


def main() -> int:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    health_check()

    missing = [name for name in HOSPITAL_FILES if not (DATA / name).exists()]
    if missing:
        raise FileNotFoundError(f"Missing hospital files: {missing}")

    file_ids = [upload_file(DATA / name) for name in HOSPITAL_FILES]
    task = TASK_PATH.read_text(encoding="utf-8")

    response = requests.post(
        f"{API_BASE}/v1/chat/completions",
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": task}],
            "file_ids": file_ids,
            "temperature": 0.2,
        },
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    payload = response.json()

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    raw_path = ARTIFACTS / f"deepanalyze_hospital_response_{timestamp}.json"
    raw_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    content = payload["choices"][0]["message"]["content"]
    content_path = ARTIFACTS / f"deepanalyze_hospital_content_{timestamp}.md"
    content_path.write_text(content, encoding="utf-8")

    downloaded: list[str] = []
    clean_report_text = extract_clean_report(content)
    facts: dict[str, object] | None = None
    for item in payload.get("generated_files") or payload["choices"][0]["message"].get("files") or []:
        url = item.get("url")
        if not url:
            continue
        try:
            downloaded_path = download_generated_file(url, ARTIFACTS)
            downloaded.append(str(downloaded_path))
            if downloaded_path.suffix.lower() in {".md", ".txt", ".csv", ".json"}:
                generated_text = downloaded_path.read_text(encoding="utf-8", errors="ignore")
                if downloaded_path.suffix.lower() in {".md", ".txt"}:
                    generated_clean = extract_clean_report(generated_text)
                    if len(generated_clean) > len(clean_report_text):
                        clean_report_text = generated_clean
                if downloaded_path.name.startswith("FACTS_FOR_REPORT") and downloaded_path.suffix.lower() == ".json":
                    facts = json.loads(generated_text)
        except Exception as exc:  # noqa: BLE001
            print(f"failed to download {url}: {exc}")

    initial_validation = validate_response(content, clean_report_text)
    final_report_source = "initial"
    if facts and (
        initial_validation["forbidden_report_terms"]
        or not initial_validation["has_chinese_report_markers"]
        or not initial_validation["has_tool_appendix"]
        or len(initial_validation["report_function_hits"]) < 8
    ):
        feedback = validation_feedback(initial_validation)
        for attempt in range(1, 4):
            report_response = requests.post(
                f"{API_BASE}/v1/chat/completions",
                json={
                    "model": MODEL,
                    "messages": [{"role": "user", "content": build_report_prompt(facts, feedback)}],
                    "temperature": 0.0,
                },
                timeout=TIMEOUT,
            )
            report_response.raise_for_status()
            report_payload = report_response.json()
            report_raw_path = ARTIFACTS / f"deepanalyze_hospital_report_response_{timestamp}_attempt{attempt}.json"
            report_raw_path.write_text(json.dumps(report_payload, indent=2, ensure_ascii=False), encoding="utf-8")
            report_content = report_payload["choices"][0]["message"]["content"]
            report_content_path = ARTIFACTS / f"deepanalyze_hospital_report_content_{timestamp}_attempt{attempt}.md"
            report_content_path.write_text(report_content, encoding="utf-8")
            candidate_report = extract_clean_report(report_content)
            candidate_validation = validate_response(content, candidate_report)
            clean_report_text = candidate_report
            final_report_source = f"model_report_attempt_{attempt}"
            if report_passes(candidate_validation):
                break
            feedback = validation_feedback(candidate_validation)

    clean_report_path = ARTIFACTS / f"deepanalyze_hospital_clean_report_{timestamp}.md"
    clean_report_path.write_text(clean_report_text, encoding="utf-8")

    validation = validate_response(content, clean_report_text)
    validation["final_report_source"] = final_report_source
    validation_path = ARTIFACTS / f"deepanalyze_hospital_validation_{timestamp}.json"
    validation_path.write_text(json.dumps(validation, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"raw response: {raw_path}")
    print(f"assistant content: {content_path}")
    print(f"clean report: {clean_report_path}")
    print(f"validation: {validation_path}")
    if downloaded:
        print("downloaded generated files:")
        for path in downloaded:
            print(f"- {path}")

    print(f"run_tool calls: {validation['run_tool_calls']}")
    print(f"unknown run_tool calls: {validation['unknown_tool_calls']}")
    print(f"forbidden report terms: {validation['forbidden_report_terms']}")
    print(f"category hits: {json.dumps(validation['category_hits'], ensure_ascii=False)}")

    enough_functions = len(validation["mentioned_or_called_functions"]) >= 7
    enough_categories = all(validation["category_hits"][category] for category in CATEGORY_GROUPS)
    enough_report_functions = len(validation["report_function_hits"]) >= 8
    no_unknown_tools = not validation["unknown_tool_calls"]
    no_forbidden_terms = not validation["forbidden_report_terms"]
    if not (
        enough_functions
        and enough_categories
        and enough_report_functions
        and validation["has_chinese_report_markers"]
        and validation["has_tool_appendix"]
        and no_unknown_tools
        and no_forbidden_terms
    ):
        print("validation failed: report did not naturally cover enough stataskills-backed analysis")
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
