from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from stataskills import run_tool


usage = []
results = {}


def summarize(value):
    if value is None:
        return "None"
    if isinstance(value, pd.DataFrame):
        return f"DataFrame shape={value.shape}"
    if isinstance(value, dict):
        parts = []
        for key, item in list(value.items())[:6]:
            if isinstance(item, (int, float, str, bool)):
                parts.append(f"{key}={item}")
            elif isinstance(item, dict):
                parts.append(f"{key}: keys={list(item)[:4]}")
            elif isinstance(item, list):
                parts.append(f"{key}: len={len(item)}")
            else:
                parts.append(f"{key}: {type(item).__name__}")
        return "; ".join(parts)
    if isinstance(value, (list, tuple)):
        return f"{type(value).__name__} len={len(value)} values={list(value)[:3]}"
    return str(value)[:180]


def markdown_table(rows):
    headers = ["Report Section", "Function", "Input Data", "Input Fields", "Purpose", "Key Output", "Success"]
    keys = ["section", "function", "data", "fields", "purpose", "key_output", "success"]

    def cell(value):
        return str(value).replace("|", "\\|").replace("\n", " ")[:500]

    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(cell(row[key]) for key in keys) + " |")
    return "\n".join(lines)


def call(section, function, data_name, fields, purpose, **kwargs):
    try:
        value = run_tool(function, **kwargs)
        success = "yes"
        key_output = summarize(value)
        results[f"{section}.{function}.{len(usage)}"] = value
    except Exception as exc:
        value = None
        success = "no"
        key_output = f"{exc.__class__.__name__}: {exc}"
    print(f"STATASKILLS_CALL: function={function}; data={data_name}; purpose={purpose}; success={success}")
    usage.append(
        {
            "section": section,
            "function": function,
            "data": data_name,
            "fields": fields,
            "purpose": purpose,
            "key_output": key_output,
            "success": success,
        }
    )
    return value


hospital = call("Data Inventory and Quality", "read_csv", "hospital_stay.csv", "all", "load hospital operations data", file="hospital_stay.csv")
whas = call("Data Inventory and Quality", "read_csv", "whas500.csv", "all", "load myocardial infarction survival data", file="whas500.csv")
chemo = call("Data Inventory and Quality", "read_csv", "chemo_data.csv", "all", "load chemotherapy survival data", file="chemo_data.csv")
biomarker = call("Data Inventory and Quality", "read_csv", "biomarker_data.csv", "all", "load biomarker survival data", file="biomarker_data.csv")
genes = call("High-dimensional Biomarker Screening", "read_csv", "gene_expression_data.csv", "all", "load high-dimensional gene expression data", file="gene_expression_data.csv")
gene_p = call("High-dimensional Biomarker Screening", "read_csv", "gene_p_values.csv", "p_value", "load gene-screen p-values", file="gene_p_values.csv")
er = call("Time Series Demand Analysis", "read_csv", "er_arrivals.csv", "all", "load hourly ER arrivals", file="er_arrivals.csv")
lalonde = call("Causal and Policy Evaluation", "read_csv", "lalonde_data.csv", "all", "load treatment-effect data", file="lalonde_data.csv")
accidents = call("Causal and Policy Evaluation", "read_csv", "accidents_did.csv", "all", "load DID accident data", file="accidents_did.csv")
gdp = call("Causal and Policy Evaluation", "read_csv", "synthetic_gdp_reform.csv", "all", "load synthetic-control GDP data", file="synthetic_gdp_reform.csv")

call("Data Inventory and Quality", "describe", "hospital_stay.csv", "Length_of_Stay_days, Patient_Age, Severity_Score", "summarize hospital operations", data=hospital, columns=["Length_of_Stay_days", "Patient_Age", "Severity_Score"])
call("Data Inventory and Quality", "check_missing_values", "hospital_stay.csv", "all", "check missingness", data=hospital)
call("Data Inventory and Quality", "detect_outliers", "hospital_stay.csv", "Length_of_Stay_days, Severity_Score", "flag operational outliers", data=hospital, columns=["Length_of_Stay_days", "Severity_Score"])
call("Data Inventory and Quality", "calculate_statistic", "hospital_stay.csv", "Length_of_Stay_days", "calculate average length of stay", data=hospital, column="Length_of_Stay_days", method="mean")
call("Clinical Operations Modeling", "correlation_analysis", "hospital_stay.csv", "Length_of_Stay_days, Severity_Score, Patient_Age", "measure clinical-operation correlations", data=hospital, method="pearson", columns=["Length_of_Stay_days", "Severity_Score", "Patient_Age"])

call("Clinical Operations Modeling", "multivariable_linear_regression", "hospital_stay.csv", "Length_of_Stay_days ~ Patient_Age + Severity_Score + Is_Surgical", "OLS length-of-stay model", data=hospital, y_col="Length_of_Stay_days", x_cols=["Patient_Age", "Severity_Score", "Is_Surgical"])
call("Clinical Operations Modeling", "run_glm", "hospital_stay.csv", "Length_of_Stay_days ~ Patient_Age + Severity_Score + Is_Surgical", "Gaussian GLM length-of-stay model", data=hospital, y_col="Length_of_Stay_days", x_cols=["Patient_Age", "Severity_Score", "Is_Surgical"], method="gaussian")
call("Clinical Operations Modeling", "huber_regression", "hospital_stay.csv", "Length_of_Stay_days ~ Patient_Age + Severity_Score + Is_Surgical", "robust regression against outliers", data=hospital, y_col="Length_of_Stay_days", x_cols=["Patient_Age", "Severity_Score", "Is_Surgical"])

call("Survival and Biomarker Analysis", "kaplan_meier_plot", "whas500.csv", "LENFOL, FSTAT, TECHNIQUE", "estimate survival curves by technique", data=whas, duration_col="LENFOL", event_col="FSTAT", group_col="TECHNIQUE")
call("Survival and Biomarker Analysis", "logrank_test_compare", "chemo_data.csv", "time, status, group", "compare treatment and control survival", data=chemo, duration_col="time", event_col="status", group_col="group")
call("Survival and Biomarker Analysis", "fit_cox_model", "whas500.csv", "LENFOL, FSTAT, AGE, BMI, HR", "fit Cox proportional hazards model", data=whas, duration_col="LENFOL", event_col="FSTAT", covariates=["AGE", "BMI", "HR"])
call("Survival and Biomarker Analysis", "kaplan_meier_plot", "biomarker_data.csv", "time_to_event, status, biomarker", "estimate survival by biomarker", data=biomarker, duration_col="time_to_event", event_col="status", group_col="biomarker")

gene_model = genes[[f"gene_expression_{i}" for i in range(30)] + ["drug_response"]].copy()
call("High-dimensional Biomarker Screening", "advanced_regression", "gene_expression_data.csv", "gene_expression_0..29 -> drug_response", "high-dimensional predictive model", data=gene_model, target="drug_response", method="ridge", test_size=0.25)
call("High-dimensional Biomarker Screening", "sparse_pca_analysis", "gene_expression_data.csv", "gene_expression_0..29", "extract sparse latent biomarker components", data=gene_model.drop(columns=["drug_response"]), n_components=3)
call("High-dimensional Biomarker Screening", "fdr_control_df", "gene_p_values.csv", "p_value", "control false discovery rate", data=gene_p, pval_col="p_value", method="bh")
call("High-dimensional Biomarker Screening", "fwer_control_df", "gene_p_values.csv", "p_value", "control family-wise error rate", data=gene_p, pval_col="p_value", method="holm")
call("High-dimensional Biomarker Screening", "bayesian_inference", "gene_p_values.csv", "successes/trials summary", "Bayesian posterior for discovery rate", model="binomial", data={"successes": int((gene_p["p_value"] < 0.05).sum()), "trials": int(len(gene_p))}, prior={"alpha": 2, "beta": 2})

call("Time Series Demand Analysis", "test_stationarity", "er_arrivals.csv", "Patient_Arrivals", "ADF stationarity test", data=er, column="Patient_Arrivals", method="adf")
call("Time Series Demand Analysis", "decompose_stl", "er_arrivals.csv", "Patient_Arrivals", "STL decomposition of hourly demand", data=er, column="Patient_Arrivals", period=24)
call("Time Series Demand Analysis", "auto_arima_modeling", "er_arrivals.csv", "Patient_Arrivals", "automatic ARIMA demand model", data=er, column="Patient_Arrivals", seasonal=False, m=1)

call("Causal and Policy Evaluation", "estimate_ATT_with_psm", "lalonde_data.csv", "treat, re78, age, educ, re74, re75", "estimate treatment effect with PSM", data=lalonde, treatment="treat", outcome="re78", covariates=["age", "educ", "re74", "re75"], caliper=0.2)
call("Causal and Policy Evaluation", "estimate_did_effect", "accidents_did.csv", "accidents, treat, year", "estimate policy effect using DID", data=accidents, outcome="accidents", treat_col="treat", time_col="year", post_year=2020, placebo_year=2019)
call("Causal and Policy Evaluation", "synthetic_control", "synthetic_gdp_reform.csv", "country, year, GDP", "estimate synthetic-control intervention effect", df=gdp, time_col="year", unit_col="country", outcome_col="GDP", treated_unit="Country_X", intervention_time=2000, control_units=["Country_1", "Country_2", "Country_3", "Country_4"])

usage_df = pd.DataFrame(usage)
usage_df.to_csv("stataskills_showcase_usage.csv", index=False)

report = []
report.append("# Clinical Operations, Survival, Biomarker Screening, and Policy Evaluation Report")
report.append("")
report.append("## Executive Summary")
report.append("This showcase ran a multi-domain statistical workflow with `stataskills.run_tool`, spanning data quality, clinical operations modeling, survival analysis, high-dimensional biomarker screening, time series demand analysis, and causal/policy evaluation.")
report.append("")
report.append("## Data Inventory and Quality")
report.append("The workflow loaded hospital operations, myocardial infarction survival, chemotherapy, biomarker, gene expression, ER demand, treatment-effect, DID, and synthetic-control datasets. Missingness, outlier checks, descriptive statistics, and basic statistics were performed with stataskills.")
report.append("")
report.append("## Clinical Operations Modeling")
report.append("Length of stay was modeled using OLS, Gaussian GLM, and Huber robust regression with patient age, severity, and surgery status as predictors.")
report.append("")
report.append("## Survival and Biomarker Analysis")
report.append("Kaplan-Meier survival summaries, log-rank testing, and Cox proportional hazards modeling were used to evaluate technique, chemotherapy group, and biomarker-associated survival patterns.")
report.append("")
report.append("## High-dimensional Biomarker Screening")
report.append("The workflow used high-dimensional regression, sparse PCA, FDR control, FWER control, and a Bayesian binomial posterior over discovery counts.")
report.append("")
report.append("## Time Series Demand Analysis")
report.append("Hourly ER arrivals were assessed with stationarity testing, STL decomposition, and automatic ARIMA modeling.")
report.append("")
report.append("## Causal and Policy Evaluation")
report.append("Treatment and policy effects were evaluated with propensity score matching, difference-in-differences, and synthetic control.")
report.append("")
report.append("## Stataskills Function Usage")
report.append(markdown_table(usage))
report.append("")
report.append("## Limitations")
report.append("This is a showcase analysis. The datasets represent different domains and should not be interpreted as one unified clinical trial. Some results are screening-level and require domain validation before decision-making.")
report.append("")
report.append("## Reproducibility Notes")
report.append("All toolkit calls were executed through `stataskills.run_tool`. Audit lines beginning with `STATASKILLS_CALL:` were printed during execution, and `stataskills_showcase_usage.csv` stores the function-use matrix.")

Path("stataskills_showcase_results.json").write_text(json.dumps({k: summarize(v) for k, v in results.items()}, indent=2), encoding="utf-8")
Path("stataskills_showcase_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
print("Saved stataskills_showcase_report.md")
print("Saved stataskills_showcase_usage.csv")
print("Saved stataskills_showcase_results.json")
