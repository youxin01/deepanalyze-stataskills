#!/usr/bin/env python3
"""
Run a WebUI v2 stataskills smoke/demo task through the chat_v2 backend.

This script does not rewrite model output. It uploads the same demo files used
by the release examples, streams the backend response, and validates that the
WebUI pipeline produced code execution and at least one stataskills.run_tool
call.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from pathlib import Path
from typing import Any

import requests
from stataskills import ALIASES, list_tools


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "datasets83"
EXAMPLES = ROOT / "examples"
ARTIFACTS = ROOT / "artifacts" / "webui"

DEFAULT_API_BASE = os.getenv("WEBUI_API_BASE", "http://localhost:8200")
DEFAULT_MODEL = os.getenv("WEBUI_MODEL", "DeepAnalyze-8B")
DEFAULT_PROVIDER = os.getenv("WEBUI_PROVIDER", "local")
DEFAULT_CUSTOM_API_BASE = os.getenv("WEBUI_CUSTOM_API_BASE", "")
DEFAULT_API_KEY = os.getenv("WEBUI_API_KEY", "")
TIMEOUT = 900

ALLOWED_TOOLS = {tool["name"] for tool in list_tools()} | set(ALIASES)

CUSTOM_MODEL_SYSTEM_PREFIX = """# Role

You are an intelligent agent designed for data analysis. You must use these
XML-style tags exactly:

- <Analyze>...</Analyze> for reasoning and planning.
- <Code>...</Code> for standalone Python code to execute.
- <Understand>...</Understand> for interpreting execution output.
- <Answer>...</Answer> for the final user-facing answer.

After outputting </Code>, stop. The system will execute the code and return the
result as a user message starting with "# Execute Result\\n". Read that result
before deciding whether to write more code or produce <Answer>.
"""

TASKS: dict[str, dict[str, Any]] = {
    "growth": {
        "prompt_file": "deepanalyze_growth_task.md",
        "data_files": ("conversion_data.csv", "website_session_data.csv"),
        "core_tools": ("ab_ttest", "contingency_test", "bootstrap_abtest"),
    },
    "hospital": {
        "prompt_file": "deepanalyze_hospital_task.md",
        "data_files": ("hospital_stay.csv", "er_arrivals.csv"),
        "core_tools": (
            "correlation_analysis",
            "simple_linear_regression",
            "multivariable_linear_regression",
        ),
    },
    "policy": {
        "prompt_file": "deepanalyze_policy_task.md",
        "data_files": ("accidents_did.csv",),
        "core_tools": ("estimate_did_effect",),
    },
}


def extract_answer(text: str) -> str:
    answers = re.findall(r"<Answer>\s*(.*?)\s*</Answer>", text, flags=re.DOTALL)
    return answers[-1].strip() if answers else ""


def iter_stream_chunks(response: requests.Response) -> tuple[list[dict[str, Any]], str | None]:
    chunks: list[dict[str, Any]] = []
    try:
        for raw_line in response.iter_lines(decode_unicode=True):
            if not raw_line:
                continue
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("data:"):
                line = line[5:].strip()
            if line == "[DONE]":
                break
            try:
                chunks.append(json.loads(line))
            except json.JSONDecodeError:
                chunks.append({"raw": line})
    except requests.RequestException as exc:
        return chunks, format_requests_error(exc)
    return chunks, None


def collect_content(chunks: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for chunk in chunks:
        choices = chunk.get("choices") if isinstance(chunk, dict) else None
        if not choices:
            continue
        delta = choices[0].get("delta") or {}
        content = delta.get("content")
        if content:
            parts.append(str(content))
    return "".join(parts)


def validate(task_name: str, raw_text: str) -> dict[str, Any]:
    task = TASKS[task_name]
    run_tool_calls = sorted(set(re.findall(r"run_tool\(\s*[\"']([^\"']+)[\"']", raw_text)))
    canonical_calls = sorted({ALIASES.get(tool, tool) for tool in run_tool_calls})
    unknown_tools = sorted(set(run_tool_calls) - ALLOWED_TOOLS)
    core_seen = sorted(set(task["core_tools"]) & set(canonical_calls))
    failures: list[str] = []
    warnings: list[str] = []

    if not run_tool_calls:
        failures.append("no stataskills.run_tool calls found")
    if "<Execute>" not in raw_text:
        failures.append("no <Execute> section found")
    if "<Answer>" not in raw_text:
        failures.append("no <Answer> section found")
    if re.search(r"No module named ['\"]stataskills|ModuleNotFoundError", raw_text):
        failures.append("stataskills import failed during execution")
    if unknown_tools:
        warnings.append(f"unknown stataskills tools attempted: {unknown_tools}")
    if run_tool_calls and not core_seen:
        warnings.append(f"core task tools not observed; expected one of {list(task['core_tools'])}")

    return {
        "task": task_name,
        "run_tool_calls": run_tool_calls,
        "canonical_run_tool_calls": canonical_calls,
        "core_tools_seen": core_seen,
        "unknown_tools": unknown_tools,
        "has_execute": "<Execute>" in raw_text,
        "has_answer": "<Answer>" in raw_text,
        "answer_chars": len(extract_answer(raw_text)),
        "failures": failures,
        "warnings": warnings,
        "passed": not failures,
    }


def format_requests_error(exc: BaseException) -> str:
    message = str(exc)
    response = getattr(exc, "response", None)
    if response is not None:
        try:
            body = response.text.strip()
        except Exception:
            body = ""
        if body:
            message = f"{message}: {body[:2000]}"
    return message


def upload_files(api_base: str, session_id: str, file_names: tuple[str, ...]) -> None:
    files = []
    handles = []
    try:
        for file_name in file_names:
            path = DATA / file_name
            handle = path.open("rb")
            handles.append(handle)
            files.append(("files", (path.name, handle, "text/csv")))
        response = requests.post(
            f"{api_base}/workspace/upload",
            params={"session_id": session_id},
            files=files,
            timeout=120,
        )
        response.raise_for_status()
    finally:
        for handle in handles:
            handle.close()


def run_task(args: argparse.Namespace) -> dict[str, Any]:
    task = TASKS[args.task]
    session_id = args.session_id or f"webui-stataskills-{args.task}-{int(time.time())}"
    task_dir = ARTIFACTS / args.task / session_id
    task_dir.mkdir(parents=True, exist_ok=True)

    requests.post(
        f"{args.api_base}/workspace/clear",
        params={"session_id": session_id},
        timeout=30,
    )
    upload_files(args.api_base, session_id, task["data_files"])

    prompt = (EXAMPLES / task["prompt_file"]).read_text(encoding="utf-8")
    messages: list[dict[str, str]] = []
    if args.provider == "custom" and args.include_custom_system_prompt:
        messages.append({"role": "system", "content": CUSTOM_MODEL_SYSTEM_PREFIX})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": args.model,
        "provider": args.provider,
        "api_base": args.custom_api_base if args.provider == "custom" else "",
        "api_key": args.api_key if args.provider in {"custom", "heywhale"} else "",
        "temperature": args.temperature,
        "session_id": session_id,
        "workspace": list(task["data_files"]),
        "messages": messages,
    }
    redacted_payload = dict(payload)
    if redacted_payload.get("api_key"):
        redacted_payload["api_key"] = "***"

    (task_dir / "request.json").write_text(
        json.dumps(redacted_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    chunks: list[dict[str, Any]] = []
    stream_error: str | None = None
    try:
        response = requests.post(
            f"{args.api_base}/chat/completions",
            json=payload,
            stream=True,
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        chunks, stream_error = iter_stream_chunks(response)
    except requests.RequestException as exc:
        stream_error = format_requests_error(exc)

    raw_text = collect_content(chunks)
    answer = extract_answer(raw_text)
    validation = validate(args.task, raw_text)
    validation["session_id"] = session_id
    validation["request"] = redacted_payload
    validation["stream_error"] = stream_error
    if stream_error:
        validation["failures"].append(f"stream error: {stream_error}")
        validation["passed"] = False

    (task_dir / "stream_chunks.jsonl").write_text(
        "\n".join(json.dumps(chunk, ensure_ascii=False) for chunk in chunks) + "\n",
        encoding="utf-8",
    )
    (task_dir / "raw.md").write_text(raw_text, encoding="utf-8")
    (task_dir / "answer.md").write_text(answer, encoding="utf-8")
    (task_dir / "validation.json").write_text(
        json.dumps(validation, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(validation, indent=2, ensure_ascii=False))
    print(f"Artifacts: {task_dir}")
    return validation


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run WebUI stataskills demo task.")
    parser.add_argument("--task", choices=sorted(TASKS), default="growth")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE)
    parser.add_argument("--provider", choices=("local", "heywhale", "custom"), default=DEFAULT_PROVIDER)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--custom-api-base", default=DEFAULT_CUSTOM_API_BASE)
    parser.add_argument("--api-key", default=DEFAULT_API_KEY)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--session-id", default="")
    parser.add_argument(
        "--no-custom-system-prompt",
        dest="include_custom_system_prompt",
        action="store_false",
        help="Do not add the frontend-like structured system prompt for custom models.",
    )
    parser.set_defaults(include_custom_system_prompt=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.provider == "custom" and not args.custom_api_base:
        raise SystemExit("--custom-api-base is required for --provider custom")
    validation = run_task(args)
    return 0 if validation["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
