#!/usr/bin/env python3
"""
Run the DeepAnalyze showcase task and download the generated Markdown report.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from urllib.parse import urlparse

import requests


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "datasets83"
ARTIFACTS = ROOT / "artifacts"
TASK_PATH = ROOT / "examples" / "deepanalyze_showcase_task.md"

API_BASE = "http://localhost:8200"
MODEL = "DeepAnalyze-8B"
TIMEOUT = 900

SHOWCASE_FILES = [
    "deepanalyze_showcase_driver.py",
    "hospital_stay.csv",
    "whas500.csv",
    "chemo_data.csv",
    "biomarker_data.csv",
    "gene_expression_data.csv",
    "gene_p_values.csv",
    "er_arrivals.csv",
    "lalonde_data.csv",
    "accidents_did.csv",
    "synthetic_gdp_reform.csv",
]

REQUIRED_FUNCTIONS = [
    "read_csv",
    "describe",
    "check_missing_values",
    "detect_outliers",
    "calculate_statistic",
    "correlation_analysis",
    "multivariable_linear_regression",
    "run_glm",
    "huber_regression",
    "advanced_regression",
    "sparse_pca_analysis",
    "test_stationarity",
    "decompose_stl",
    "auto_arima_modeling",
    "kaplan_meier_plot",
    "logrank_test_compare",
    "fit_cox_model",
    "fdr_control_df",
    "fwer_control_df",
    "bayesian_inference",
    "estimate_ATT_with_psm",
    "estimate_did_effect",
    "synthetic_control",
]


def health_check() -> None:
    response = requests.get(f"{API_BASE}/health", timeout=10)
    response.raise_for_status()


def upload_file(path: Path) -> str:
    content_type = "text/x-python" if path.suffix == ".py" else "text/csv"
    with path.open("rb") as handle:
        response = requests.post(
            f"{API_BASE}/v1/files",
            files={"file": (path.name, handle, content_type)},
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


def validate_response(content: str) -> dict[str, object]:
    mentioned = sorted({fn for fn in REQUIRED_FUNCTIONS if re.search(rf"\b{re.escape(fn)}\b", content)})
    audit_lines = re.findall(r"^STATASKILLS_CALL: function=[^{};]+;.*$", content, flags=re.MULTILINE)
    return {
        "required_functions": REQUIRED_FUNCTIONS,
        "mentioned_functions": mentioned,
        "missing_functions": sorted(set(REQUIRED_FUNCTIONS) - set(mentioned)),
        "audit_line_count": len(audit_lines),
        "audit_lines": audit_lines,
    }


def main() -> int:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    health_check()

    missing_files = []
    for name in SHOWCASE_FILES:
        path = (ROOT / "examples" / name) if name.endswith(".py") else (DATA / name)
        if not path.exists():
            missing_files.append(name)
    if missing_files:
        raise FileNotFoundError(f"Missing showcase files: {missing_files}")

    file_ids = [
        upload_file((ROOT / "examples" / name) if name.endswith(".py") else (DATA / name))
        for name in SHOWCASE_FILES
    ]
    task = TASK_PATH.read_text(encoding="utf-8")

    response = requests.post(
        f"{API_BASE}/v1/chat/completions",
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": task}],
            "file_ids": file_ids,
            "temperature": 0.1,
        },
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    payload = response.json()

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    raw_path = ARTIFACTS / f"deepanalyze_showcase_response_{timestamp}.json"
    raw_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    content = payload["choices"][0]["message"]["content"]
    content_path = ARTIFACTS / f"deepanalyze_showcase_content_{timestamp}.md"
    content_path.write_text(content, encoding="utf-8")

    downloaded: list[str] = []
    validation_text = content
    for item in payload.get("generated_files") or payload["choices"][0]["message"].get("files") or []:
        url = item.get("url")
        if not url:
            continue
        try:
            downloaded_path = download_generated_file(url, ARTIFACTS)
            downloaded.append(str(downloaded_path))
            if downloaded_path.suffix.lower() in {".md", ".txt", ".csv", ".json"}:
                validation_text += "\n" + downloaded_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as exc:  # noqa: BLE001 - preserve report even if download fails
            print(f"failed to download {url}: {exc}")

    validation = validate_response(validation_text)
    validation_path = ARTIFACTS / f"deepanalyze_showcase_validation_{timestamp}.json"
    validation_path.write_text(json.dumps(validation, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"raw response: {raw_path}")
    print(f"assistant content: {content_path}")
    print(f"validation: {validation_path}")
    if downloaded:
        print("downloaded generated files:")
        for path in downloaded:
            print(f"- {path}")

    print(f"mentioned functions: {len(validation['mentioned_functions'])} / {len(REQUIRED_FUNCTIONS)}")
    if validation["missing_functions"]:
        print("missing function mentions:")
        for fn in validation["missing_functions"]:
            print(f"- {fn}")
        return 2
    if validation["audit_line_count"] < len(REQUIRED_FUNCTIONS):
        print(
            "not enough real STATASKILLS_CALL audit lines: "
            f"{validation['audit_line_count']} / {len(REQUIRED_FUNCTIONS)}"
        )
        return 3

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
