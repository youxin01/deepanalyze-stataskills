#!/usr/bin/env python3
"""
Run the three DeepAnalyze demo tasks and save original model reports.

This runner intentionally does not rewrite, polish, or synthesize reports. It
only extracts the model's own final answer when an <Answer> block exists.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import requests
from stataskills import ALIASES, list_tools


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "datasets83"
REPORTS = ROOT / "artifacts" / "reports"
GENERATED = REPORTS / "generated"

API_BASE = "http://localhost:8200"
MODEL = "DeepAnalyze-8B"
TIMEOUT = 900

ALLOWED_TOOLS = {tool["name"] for tool in list_tools()} | set(ALIASES)


@dataclass(frozen=True)
class DemoTask:
    name: str
    task_file: str
    data_files: tuple[str, ...]
    core_tools: tuple[str, ...]
    forbidden_terms: tuple[str, ...] = ()


TASKS: dict[str, DemoTask] = {
    "hospital": DemoTask(
        name="hospital",
        task_file="deepanalyze_hospital_task.md",
        data_files=("hospital_stay.csv", "er_arrivals.csv"),
        core_tools=(
            "correlation_analysis",
            "simple_linear_regression",
            "multivariable_linear_regression",
            "test_stationarity",
        ),
        forbidden_terms=("5年生存率", "药物组", "支架", "不良反应", "糖尿病", "心梗", "化疗"),
    ),
    "growth": DemoTask(
        name="growth",
        task_file="deepanalyze_growth_task.md",
        data_files=("conversion_data.csv", "website_session_data.csv"),
        core_tools=(
            "contingency_test",
            "ab_ttest",
            "bootstrap_abtest",
        ),
        forbidden_terms=("证明提升", "导致转化", "因果证明"),
    ),
    "policy": DemoTask(
        name="policy",
        task_file="deepanalyze_policy_task.md",
        data_files=("accidents_did.csv",),
        core_tools=(
            "estimate_did_effect",
        ),
        forbidden_terms=("随机实验证明", "placebo证明政策有效", "安慰剂政策效果"),
    ),
}


def extract_clean_report(text: str) -> str:
    answers = re.findall(r"<Answer>\s*(.*?)\s*</Answer>", text, flags=re.DOTALL)
    if answers:
        return answers[-1].strip()
    clean = text
    for marker in ("\\newpage", "# 附录：完整对话过程", "## 对话轮次"):
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
    return response.json()["id"]


def download_generated_file(url: str, output_dir: Path) -> Path:
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    parsed = urlparse(url)
    name = Path(parsed.path).name or f"generated_{int(time.time())}.dat"
    target = output_dir / name
    if target.exists():
        target = output_dir / f"{int(time.time())}_{name}"
    target.write_bytes(response.content)
    return target


def validate(task: DemoTask, raw_text: str, report_text: str) -> dict[str, object]:
    run_tool_calls = sorted(set(re.findall(r"run_tool\(\s*[\"']([^\"']+)[\"']", raw_text)))
    canonical_calls = sorted({ALIASES.get(tool, tool) for tool in run_tool_calls})
    unknown_tools = sorted(set(run_tool_calls) - ALLOWED_TOOLS)
    core_seen = sorted(set(task.core_tools) & set(canonical_calls))
    non_read_tools_seen = sorted(tool for tool in canonical_calls if tool != "read_csv")
    forbidden_terms = sorted(term for term in task.forbidden_terms if term in report_text)
    failed_checks: list[str] = []
    warnings: list[str] = []

    if unknown_tools:
        warnings.append(f"unknown stataskills tools attempted in raw output: {unknown_tools}")
    if not canonical_calls:
        failed_checks.append("no stataskills run_tool calls observed in raw output")
    elif not non_read_tools_seen:
        warnings.append("only read_csv was observed; no non-read stataskills tools were observed")
    elif not core_seen:
        warnings.append(f"core task tools not observed; expected one of: {list(task.core_tools)}")
    if forbidden_terms:
        failed_checks.append(f"forbidden report terms: {forbidden_terms}")
    if not report_text:
        failed_checks.append("empty clean report")

    return {
        "task": task.name,
        "core_tools": list(task.core_tools),
        "run_tool_calls": run_tool_calls,
        "canonical_run_tool_calls": canonical_calls,
        "core_tools_seen": core_seen,
        "non_read_tools_seen": non_read_tools_seen,
        "unknown_tools": unknown_tools,
        "forbidden_terms": forbidden_terms,
        "failed_checks": failed_checks,
        "warnings": warnings,
        "passed": not failed_checks,
        "raw_chars": len(raw_text),
        "report_chars": len(report_text),
    }


def run_task(task: DemoTask) -> dict[str, object]:
    REPORTS.mkdir(parents=True, exist_ok=True)
    task_generated_dir = GENERATED / task.name
    task_generated_dir.mkdir(parents=True, exist_ok=True)

    missing = [name for name in task.data_files if not (DATA / name).exists()]
    if missing:
        raise FileNotFoundError(f"{task.name}: missing data files: {missing}")

    task_path = ROOT / "examples" / task.task_file
    task_prompt = task_path.read_text(encoding="utf-8")
    file_ids = []
    for file_name in task.data_files:
        file_id = upload_file(DATA / file_name)
        print(f"{task.name}: uploaded {file_name}: {file_id}")
        file_ids.append(file_id)

    response = requests.post(
        f"{API_BASE}/v1/chat/completions",
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": task_prompt}],
            "file_ids": file_ids,
            "temperature": 0.2,
        },
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    payload = response.json()

    raw_text = payload["choices"][0]["message"]["content"]
    clean_report = extract_clean_report(raw_text)

    downloaded: list[str] = []
    for item in payload.get("generated_files") or payload["choices"][0]["message"].get("files") or []:
        url = item.get("url")
        if not url:
            continue
        try:
            downloaded_path = download_generated_file(url, task_generated_dir)
            downloaded.append(str(downloaded_path))
        except Exception as exc:  # noqa: BLE001
            downloaded.append(f"failed:{url}:{exc}")

    (REPORTS / f"{task.name}.md").write_text(clean_report, encoding="utf-8")
    (REPORTS / f"{task.name}_raw.md").write_text(raw_text, encoding="utf-8")
    (REPORTS / f"{task.name}_response.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    validation = validate(task, raw_text, clean_report)
    validation["downloaded_generated_files"] = downloaded
    (REPORTS / f"{task.name}_validation.json").write_text(
        json.dumps(validation, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"{task.name}: report {REPORTS / f'{task.name}.md'}")
    print(f"{task.name}: validation passed={validation['passed']}")
    if validation["failed_checks"]:
        print(f"{task.name}: failed checks: {validation['failed_checks']}")
    if validation["warnings"]:
        print(f"{task.name}: warnings: {validation['warnings']}")
    return validation


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run DeepAnalyze demo tasks.")
    parser.add_argument(
        "--task",
        choices=["all", *TASKS.keys()],
        default="all",
        help="Task to run. Defaults to all.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    health_check()
    selected = TASKS.keys() if args.task == "all" else [args.task]
    validations = [run_task(TASKS[name]) for name in selected]
    summary = {
        "tasks": [item["task"] for item in validations],
        "passed": {item["task"]: item["passed"] for item in validations},
        "report_dir": str(REPORTS),
    }
    (REPORTS / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
