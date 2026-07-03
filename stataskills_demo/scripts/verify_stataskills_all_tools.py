#!/usr/bin/env python3
"""
Verify that every public stataskills tool can be called successfully.

This is intentionally a plain Python script rather than pytest so it can run in
DeepAnalyze's execution environment without extra test dependencies.
"""

from __future__ import annotations

import json
import math
import tempfile
import time
import traceback
from collections import Counter
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

from stataskills import list_tools, run_tool


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "datasets83"
ARTIFACTS = ROOT / "artifacts"


def data_path(name: str) -> str:
    return str(DATA / name)


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float, np.number)) and math.isfinite(float(value))


def has_keys(*keys: str) -> Callable[[Any], None]:
    def validate(result: Any) -> None:
        if not isinstance(result, dict):
            raise AssertionError(f"expected dict, got {type(result).__name__}")
        missing = [key for key in keys if key not in result]
        if missing:
            raise AssertionError(f"missing keys: {missing}")

    return validate


def any_result(result: Any) -> None:
    if result is None:
        raise AssertionError("result is None")


def dataframe_like(result: Any) -> None:
    if isinstance(result, pd.DataFrame):
        if result.empty:
            raise AssertionError("DataFrame is empty")
        return
    if isinstance(result, dict) and result.get("type") == "DataFrame":
        if not result.get("shape"):
            raise AssertionError("DataFrame summary has no shape")
        return
    raise AssertionError(f"expected DataFrame or DataFrame summary, got {type(result).__name__}")


def finite_key(key: str) -> Callable[[Any], None]:
    def validate(result: Any) -> None:
        if not isinstance(result, dict) or key not in result:
            raise AssertionError(f"missing numeric key: {key}")
        if not finite_number(result[key]):
            raise AssertionError(f"{key} is not finite: {result[key]!r}")

    return validate


def ci_tuple(result: Any) -> None:
    if not isinstance(result, (list, tuple)) or len(result) != 2:
        raise AssertionError(f"expected length-2 interval, got {result!r}")
    if not all(finite_number(x) for x in result):
        raise AssertionError(f"interval contains non-finite values: {result!r}")
    if float(result[0]) >= float(result[1]):
        raise AssertionError(f"interval is not ordered: {result!r}")


def prepare_frames() -> dict[str, pd.DataFrame]:
    frames: dict[str, pd.DataFrame] = {}
    frames["high_dim_small"] = pd.read_csv(data_path("high_dim_regression.csv"))[
        [f"feature_{i}" for i in range(25)] + ["target"]
    ]
    frames["latent_small"] = pd.read_csv(data_path("latent_structure.csv"))[
        [f"var_{i}" for i in range(20)]
    ]
    frames["teaching_small"] = pd.read_csv(data_path("teaching_methods_data.csv")).head(80)
    frames["mantel"] = pd.DataFrame(
        {
            "exposure": [0, 0, 1, 1] * 6,
            "outcome": [0, 1, 0, 1, 0, 0, 1, 1] * 3,
            "stratum": ["low"] * 8 + ["mid"] * 8 + ["high"] * 8,
        }
    )
    frames["fisher"] = pd.DataFrame(
        {
            "treatment": ["A"] * 12 + ["B"] * 12,
            "response": [1] * 9 + [0] * 3 + [1] * 4 + [0] * 8,
        }
    )
    return frames


def build_cases(frames: dict[str, pd.DataFrame], temp_dir: Path) -> list[dict[str, Any]]:
    txt_path = temp_dir / "notes.txt"
    csv_path = temp_dir / "mini.csv"
    md_path = temp_dir / "notes.md"
    txt_path.write_text("stataskills verification text file\n", encoding="utf-8")
    csv_path.write_text("x,y\n1,2\n3,4\n", encoding="utf-8")
    md_path.write_text("# stataskills verification\n", encoding="utf-8")

    return [
        {
            "case_id": "read_csv.primary",
            "tool": "read_csv",
            "kind": "primary",
            "kwargs": {"file": data_path("hospital_stay.csv")},
            "validate": lambda r: isinstance(r, pd.DataFrame) and not r.empty,
        },
        {
            "case_id": "describe.primary",
            "tool": "describe",
            "kind": "primary",
            "kwargs": {"data": data_path("hospital_stay.csv"), "columns": ["Length_of_Stay_days"]},
            "validate": has_keys("Length_of_Stay_days"),
        },
        {
            "case_id": "calculate_statistic.primary",
            "tool": "calculate_statistic",
            "kind": "primary",
            "kwargs": {"data": data_path("advertising.csv"), "column": "Sales", "method": "mean"},
            "validate": lambda r: finite_number(r),
        },
        {
            "case_id": "check_missing_values.primary",
            "tool": "check_missing_values",
            "kind": "primary",
            "kwargs": {"data": data_path("Heart Failure Prediction Dataset.csv"), "columns": ["Age", "Cholesterol"]},
            "validate": has_keys("Age", "Cholesterol"),
        },
        {
            "case_id": "detect_outliers.primary",
            "tool": "detect_outliers",
            "kind": "primary",
            "kwargs": {"data": data_path("hospital_stay.csv"), "columns": ["Length_of_Stay_days"]},
            "validate": has_keys("Length_of_Stay_days"),
        },
        {
            "case_id": "check_column_type_is.primary",
            "tool": "check_column_type_is",
            "kind": "primary",
            "kwargs": {"data": data_path("Heart Failure Prediction Dataset.csv"), "columns": ["Sex"], "target_type": "object"},
            "validate": has_keys("Sex"),
        },
        {
            "case_id": "show_csv_info_en.primary",
            "tool": "show_csv_info_en",
            "kind": "primary",
            "kwargs": {"data": data_path("hospital_stay.csv")},
            "validate": lambda r: isinstance(r, str) and "Dataset" in r,
        },
        {
            "case_id": "read_file.primary.txt",
            "tool": "read_file",
            "kind": "primary",
            "kwargs": {"file": str(txt_path)},
            "validate": lambda r: isinstance(r, str) and "verification" in r,
        },
        {
            "case_id": "read_file.branch.csv",
            "tool": "read_file",
            "kind": "branch",
            "kwargs": {"file": str(csv_path)},
            "validate": lambda r: isinstance(r, list) and len(r) >= 2,
        },
        {
            "case_id": "read_file.branch.md",
            "tool": "read_file",
            "kind": "branch",
            "kwargs": {"file": str(md_path)},
            "validate": lambda r: isinstance(r, str) and r.startswith("#"),
        },
        {
            "case_id": "correlation_analysis.primary.pearson",
            "tool": "correlation_analysis",
            "kind": "primary",
            "kwargs": {"data": data_path("advertising.csv"), "method": "pearson", "columns": ["TV", "Radio", "Sales"]},
            "validate": dataframe_like,
        },
        {
            "case_id": "correlation_analysis.branch.partial",
            "tool": "correlation_analysis",
            "kind": "branch",
            "kwargs": {
                "data": data_path("hospital_stay.csv"),
                "method": "partial",
                "columns": ["Length_of_Stay_days", "Severity_Score"],
                "covar": "Patient_Age",
            },
            "validate": any_result,
        },
        {
            "case_id": "ci_normal.primary.mean",
            "tool": "ci_normal",
            "kind": "primary",
            "kwargs": {"param_to_estimate": "mean", "sample_mean": 10.0, "sample_std": 2.0, "n": 30},
            "validate": ci_tuple,
        },
        {
            "case_id": "ci_normal.branch.variance",
            "tool": "ci_normal",
            "kind": "branch",
            "kwargs": {"param_to_estimate": "variance", "sample_mean": 10.0, "sample_std": 2.0, "n": 30},
            "validate": ci_tuple,
        },
        {
            "case_id": "ci_two_normal.primary.mean_diff",
            "tool": "ci_two_normal",
            "kind": "primary",
            "kwargs": {
                "data_type": "mean_diff",
                "sample_mean1": 12.0,
                "sample_std1": 2.2,
                "n1": 40,
                "sample_mean2": 10.5,
                "sample_std2": 2.5,
                "n2": 35,
            },
            "validate": ci_tuple,
        },
        {
            "case_id": "ci_two_normal.branch.var_ratio",
            "tool": "ci_two_normal",
            "kind": "branch",
            "kwargs": {"data_type": "var_ratio", "sample_std1": 2.2, "n1": 40, "sample_std2": 2.5, "n2": 35},
            "validate": ci_tuple,
        },
        {
            "case_id": "contingency_test.primary.chisquare",
            "tool": "contingency_test",
            "kind": "primary",
            "kwargs": {"data": data_path("Heart Failure Prediction Dataset.csv"), "columns": ["Sex", "HeartDisease"]},
            "validate": has_keys("method", "statistic", "p_value"),
        },
        {
            "case_id": "contingency_test.branch.fisher",
            "tool": "contingency_test",
            "kind": "branch",
            "kwargs": {"data": frames["fisher"], "columns": ["treatment", "response"], "method": "fisher exact"},
            "validate": has_keys("method", "odds_ratio", "p_value"),
        },
        {
            "case_id": "contingency_test.branch.mantel",
            "tool": "contingency_test",
            "kind": "branch",
            "kwargs": {"data": frames["mantel"], "columns": ["exposure", "outcome", "stratum"], "method": "mantel-haenszel"},
            "validate": has_keys("method", "common_odds_ratio", "p_value"),
        },
        {
            "case_id": "ks_test.primary.one_sample",
            "tool": "ks_test",
            "kind": "primary",
            "kwargs": {"data": data_path("bulb_lifespan_data.csv"), "columns": ["lifespan"], "mode": "one-sample"},
            "validate": has_keys("test", "statistic", "p_value"),
        },
        {
            "case_id": "ks_test.branch.two_sample",
            "tool": "ks_test",
            "kind": "branch",
            "kwargs": {"data": data_path("diet_study.csv"), "columns": ["Weight_Before", "Weight_After"], "mode": "two-sample"},
            "validate": has_keys("test", "statistic", "p_value"),
        },
        {
            "case_id": "mood_variance_test.primary",
            "tool": "mood_variance_test",
            "kind": "primary",
            "kwargs": {"data": data_path("diet_study.csv"), "columns": ["Weight_Before", "Weight_After"]},
            "validate": has_keys("method", "statistic", "p_value"),
        },
        {
            "case_id": "nonparametric_test.primary.mannwhitney",
            "tool": "nonparametric_test",
            "kind": "primary",
            "kwargs": {"data": data_path("ab_test_satisfaction.csv"), "columns": ["A_Satisfaction", "B_Satisfaction"], "method": "mannwhitney"},
            "validate": has_keys("method", "statistic", "p_value"),
        },
        {
            "case_id": "nonparametric_test.branch.wilcoxon",
            "tool": "nonparametric_test",
            "kind": "branch",
            "kwargs": {"data": data_path("diet_study.csv"), "columns": ["Weight_Before", "Weight_After"], "method": "wilcoxon"},
            "validate": has_keys("method", "statistic", "p_value"),
        },
        {
            "case_id": "nonparametric_test.branch.kruskal",
            "tool": "nonparametric_test",
            "kind": "branch",
            "kwargs": {
                "data": data_path("diet_study2.csv"),
                "columns": ["diet_Control", "diet_Mediterranean", "diet_Atkins", "diet_Vegan"],
                "method": "kruskal",
            },
            "validate": has_keys("method", "statistic", "p_value"),
        },
        {
            "case_id": "fdr_control_df.primary.bh",
            "tool": "fdr_control_df",
            "kind": "primary",
            "kwargs": {"data": data_path("gene_p_values.csv"), "pval_col": "p_value", "method": "bh"},
            "validate": dataframe_like,
        },
        {
            "case_id": "fdr_control_df.branch.by",
            "tool": "fdr_control_df",
            "kind": "branch",
            "kwargs": {"data": data_path("p_value_dataset.csv"), "pval_col": "p_value", "method": "by"},
            "validate": dataframe_like,
        },
        {
            "case_id": "fwer_control_df.primary.bonferroni",
            "tool": "fwer_control_df",
            "kind": "primary",
            "kwargs": {"data": data_path("gene_p_values.csv"), "pval_col": "p_value", "method": "bonferroni"},
            "validate": dataframe_like,
        },
        {
            "case_id": "fwer_control_df.branch.holm",
            "tool": "fwer_control_df",
            "kind": "branch",
            "kwargs": {"data": data_path("p_value_dataset.csv"), "pval_col": "p_value", "method": "holm"},
            "validate": dataframe_like,
        },
        {
            "case_id": "simple_linear_regression.primary",
            "tool": "simple_linear_regression",
            "kind": "primary",
            "kwargs": {"data": data_path("advertising.csv"), "x_col": "TV", "y_col": "Sales"},
            "validate": has_keys("intercept", "coefficient", "r_squared"),
        },
        {
            "case_id": "multivariable_linear_regression.primary",
            "tool": "multivariable_linear_regression",
            "kind": "primary",
            "kwargs": {"data": data_path("advertising.csv"), "y_col": "Sales", "x_cols": ["TV", "Radio", "Newspaper"]},
            "validate": has_keys("coefficients", "r_squared", "adj_r_squared"),
        },
        {
            "case_id": "run_glm.primary.gaussian",
            "tool": "run_glm",
            "kind": "primary",
            "kwargs": {"data": data_path("advertising.csv"), "y_col": "Sales", "x_cols": ["TV", "Radio"], "method": "gaussian"},
            "validate": has_keys("method", "coefficients", "aic"),
        },
        {
            "case_id": "run_glm.branch.logistic",
            "tool": "run_glm",
            "kind": "branch",
            "kwargs": {
                "data": data_path("Heart Failure Prediction Dataset.csv"),
                "y_col": "HeartDisease",
                "x_cols": ["Age", "MaxHR", "Oldpeak"],
                "method": "logistic",
            },
            "validate": has_keys("method", "coefficients", "aic"),
        },
        {
            "case_id": "run_glm.branch.poisson",
            "tool": "run_glm",
            "kind": "branch",
            "kwargs": {"data": data_path("er_arrivals.csv"), "y_col": "Patient_Arrivals", "x_cols": ["Hour_of_Day", "Day_of_Week"], "method": "poisson"},
            "validate": has_keys("method", "coefficients", "aic"),
        },
        {
            "case_id": "huber_regression.primary",
            "tool": "huber_regression",
            "kind": "primary",
            "kwargs": {
                "data": data_path("hospital_stay.csv"),
                "y_col": "Length_of_Stay_days",
                "x_cols": ["Patient_Age", "Severity_Score", "Is_Surgical"],
            },
            "validate": has_keys("method", "coefficients", "scale"),
        },
        {
            "case_id": "advanced_regression.primary",
            "tool": "advanced_regression",
            "kind": "primary",
            "kwargs": {"data": frames["high_dim_small"], "target": "target", "method": "lasso", "test_size": 0.25},
            "validate": has_keys("method", "best_alpha", "coefficients", "r2"),
        },
        {
            "case_id": "sparse_pca_analysis.primary",
            "tool": "sparse_pca_analysis",
            "kind": "primary",
            "kwargs": {"data": frames["latent_small"], "n_components": 3},
            "validate": has_keys("component_matrix", "reduced_data", "top_features_per_component"),
        },
        {
            "case_id": "test_stationarity.primary.adf",
            "tool": "test_stationarity",
            "kind": "primary",
            "kwargs": {"data": data_path("gdp_growth.csv"), "column": "GDP", "method": "adf"},
            "validate": has_keys("method", "statistic", "p_value", "stationary"),
        },
        {
            "case_id": "test_stationarity.branch.kpss",
            "tool": "test_stationarity",
            "kind": "branch",
            "kwargs": {"data": data_path("gdp_growth.csv"), "column": "GDP", "method": "kpss"},
            "validate": has_keys("method", "statistic", "p_value", "stationary"),
        },
        {
            "case_id": "decompose_stl.primary",
            "tool": "decompose_stl",
            "kind": "primary",
            "kwargs": {"data": data_path("tourism.csv"), "column": "Visitors", "period": 12},
            "validate": has_keys("method", "trend_mean", "trend_std", "seasonal_mean", "resid_var"),
        },
        {
            "case_id": "auto_arima_modeling.primary",
            "tool": "auto_arima_modeling",
            "kind": "primary",
            "kwargs": {"data": data_path("tourism.csv"), "column": "Visitors", "seasonal": False, "m": 1},
            "validate": has_keys("method", "order", "aic", "bic"),
        },
        {
            "case_id": "kaplan_meier_plot.primary",
            "tool": "kaplan_meier_plot",
            "kind": "primary",
            "kwargs": {"data": data_path("whas500.csv"), "duration_col": "LENFOL", "event_col": "FSTAT", "group_col": "TECHNIQUE"},
            "validate": any_result,
        },
        {
            "case_id": "logrank_test_compare.primary",
            "tool": "logrank_test_compare",
            "kind": "primary",
            "kwargs": {"data": data_path("whas500.csv"), "duration_col": "LENFOL", "event_col": "FSTAT", "group_col": "TECHNIQUE"},
            "validate": dataframe_like,
        },
        {
            "case_id": "fit_cox_model.primary",
            "tool": "fit_cox_model",
            "kind": "primary",
            "kwargs": {"data": data_path("whas500.csv"), "duration_col": "LENFOL", "event_col": "FSTAT", "covariates": ["AGE", "BMI", "HR"]},
            "validate": has_keys("method", "coefficients", "hazard_ratios", "model_info"),
        },
        {
            "case_id": "ab_ttest.primary",
            "tool": "ab_ttest",
            "kind": "primary",
            "kwargs": {
                "data": data_path("website_session_data.csv"),
                "group_col": "group",
                "value_col": "engagement_score",
                "group_A": "A",
                "group_B": "B",
            },
            "validate": has_keys("method", "group_A_mean", "group_B_mean", "p_value"),
        },
        {
            "case_id": "bootstrap_abtest.primary",
            "tool": "bootstrap_abtest",
            "kind": "primary",
            "kwargs": {
                "data": data_path("website_session_data.csv"),
                "group_col": "group",
                "value_col": "engagement_score",
                "group_A": "A",
                "group_B": "B",
            },
            "validate": has_keys("method", "observed_difference", "ci_lower", "ci_upper", "significant"),
        },
        {
            "case_id": "ab_power_analysis.primary.proportion",
            "tool": "ab_power_analysis",
            "kind": "primary",
            "kwargs": {"test_type": "proportion", "baseline": 0.08, "effect": 0.02, "power": 0.8},
            "validate": lambda r: isinstance(r, int) and r > 0,
        },
        {
            "case_id": "ab_power_analysis.branch.mean",
            "tool": "ab_power_analysis",
            "kind": "branch",
            "kwargs": {"test_type": "mean", "effect": 2.0, "std_dev": 8.0, "power": 0.8},
            "validate": lambda r: isinstance(r, int) and r > 0,
        },
        {
            "case_id": "bayesian_inference.primary.binomial",
            "tool": "bayesian_inference",
            "kind": "primary",
            "kwargs": {"model": "binomial", "data": {"successes": 62, "trials": 100}, "prior": {"alpha": 2, "beta": 2}},
            "validate": has_keys("posterior_mean", "credible_interval", "posterior_dist"),
        },
        {
            "case_id": "bayesian_inference.branch.normal",
            "tool": "bayesian_inference",
            "kind": "branch",
            "kwargs": {"model": "normal", "data": {"mean": 5.2, "n": 80, "std": 1.4}, "prior": {"mu0": 5.0, "sigma0": 2.0}},
            "validate": has_keys("posterior_mean", "credible_interval", "posterior_dist"),
        },
        {
            "case_id": "bayesian_linear_regression.primary",
            "tool": "bayesian_linear_regression",
            "kind": "primary",
            "kwargs": {"data": data_path("hospital_stay.csv"), "target": "Length_of_Stay_days", "predictor": "Severity_Score"},
            "validate": has_keys("method", "posterior_mean", "posterior_std", "credible_interval"),
        },
        {
            "case_id": "fit_hierarchical_model.primary",
            "tool": "fit_hierarchical_model",
            "kind": "primary",
            "kwargs": {
                "data": frames["teaching_small"],
                "group_col": "school_id",
                "outcome_col": "score",
                "predictor_col": "treatment",
                "model_type": "normal",
                "draws": 20,
                "tune": 20,
            },
            "validate": has_keys("model", "trace", "summary"),
        },
        {
            "case_id": "estimate_ATT_with_psm.primary",
            "tool": "estimate_ATT_with_psm",
            "kind": "primary",
            "kwargs": {
                "data": data_path("lalonde_data.csv"),
                "treatment": "treat",
                "outcome": "re78",
                "covariates": ["age", "educ", "re74", "re75"],
                "caliper": 0.2,
            },
            "validate": has_keys("ATT", "n_matched", "matched_data"),
        },
        {
            "case_id": "estimate_did_effect.primary",
            "tool": "estimate_did_effect",
            "kind": "primary",
            "kwargs": {
                "data": data_path("accidents_did.csv"),
                "outcome": "accidents",
                "treat_col": "treat",
                "time_col": "year",
                "post_year": 2020,
                "placebo_year": 2019,
            },
            "validate": has_keys("DID_coefficient", "p_value", "conf_int", "placebo"),
        },
        {
            "case_id": "synthetic_control.primary",
            "tool": "synthetic_control",
            "kind": "primary",
            "kwargs": {
                "df": data_path("synthetic_gdp_reform.csv"),
                "time_col": "year",
                "unit_col": "country",
                "outcome_col": "GDP",
                "treated_unit": "Country_X",
                "intervention_time": 2000,
                "control_units": ["Country_1", "Country_2", "Country_3", "Country_4"],
            },
            "validate": has_keys("time", "treated", "synthetic", "treatment_effect", "weights"),
        },
    ]


def summarize_result(result: Any) -> str:
    if isinstance(result, pd.DataFrame):
        return f"DataFrame shape={result.shape}"
    if isinstance(result, dict):
        keys = list(result.keys())[:8]
        return f"dict keys={keys}"
    if isinstance(result, (list, tuple)):
        return f"{type(result).__name__} len={len(result)}"
    return repr(result)[:160]


def run_case(case: dict[str, Any]) -> dict[str, Any]:
    started = time.perf_counter()
    record = {
        "case_id": case["case_id"],
        "tool": case["tool"],
        "kind": case["kind"],
        "status": "FAIL",
        "duration_sec": None,
        "summary": "",
        "error": "",
    }
    try:
        result = run_tool(case["tool"], **case["kwargs"])
        case["validate"](result)
        record["status"] = "PASS"
        record["summary"] = summarize_result(result)
    except Exception as exc:  # noqa: BLE001 - this is a verification harness
        record["error"] = f"{exc.__class__.__name__}: {exc}"
        record["traceback"] = traceback.format_exc()
    finally:
        record["duration_sec"] = round(time.perf_counter() - started, 3)
    return record


def write_reports(records: list[dict[str, Any]], public_tools: set[str]) -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    json_path = ARTIFACTS / "stataskills_call_matrix.json"
    md_path = ARTIFACTS / "stataskills_call_matrix.md"

    status_counts = Counter(record["status"] for record in records)
    primary_passed = {r["tool"] for r in records if r["kind"] == "primary" and r["status"] == "PASS"}
    missing_primary = sorted(public_tools - primary_passed)

    payload = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "summary": {
            "total_cases": len(records),
            "passed": status_counts.get("PASS", 0),
            "failed": status_counts.get("FAIL", 0),
            "public_tools": len(public_tools),
            "public_tools_with_primary_pass": len(primary_passed),
            "missing_primary_tools": missing_primary,
        },
        "records": records,
    }
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# Stataskills Call Matrix",
        "",
        f"- Total cases: {len(records)}",
        f"- Passed: {status_counts.get('PASS', 0)}",
        f"- Failed: {status_counts.get('FAIL', 0)}",
        f"- Public tools with primary PASS: {len(primary_passed)} / {len(public_tools)}",
        "",
    ]
    if missing_primary:
        lines.extend(["## Missing Primary Tool Coverage", "", ", ".join(missing_primary), ""])
    lines.extend(
        [
            "## Cases",
            "",
            "| Status | Kind | Tool | Case | Seconds | Summary / Error |",
            "|---|---|---|---|---:|---|",
        ]
    )
    for record in records:
        detail = record["summary"] if record["status"] == "PASS" else record["error"]
        detail = str(detail).replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| {record['status']} | {record['kind']} | `{record['tool']}` | "
            f"`{record['case_id']}` | {record['duration_sec']} | {detail} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    public_tools = {tool["name"] for tool in list_tools()}
    with tempfile.TemporaryDirectory(prefix="stataskills_verify_") as tmp:
        frames = prepare_frames()
        cases = build_cases(frames, Path(tmp))
        records = [run_case(case) for case in cases]

    write_reports(records, public_tools)

    failed = [record for record in records if record["status"] != "PASS"]
    missing = sorted(public_tools - {r["tool"] for r in records if r["kind"] == "primary" and r["status"] == "PASS"})

    print(f"Total cases: {len(records)}")
    print(f"Passed: {len(records) - len(failed)}")
    print(f"Failed: {len(failed)}")
    print(f"Public tools covered by primary PASS: {len(public_tools) - len(missing)} / {len(public_tools)}")
    print(f"Artifacts: {ARTIFACTS / 'stataskills_call_matrix.md'}")

    if failed:
        print("\nFailures:")
        for record in failed:
            print(f"- {record['case_id']}: {record['error']}")
    if missing:
        print("\nMissing primary coverage:")
        for tool in missing:
            print(f"- {tool}")

    return 1 if failed or missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
