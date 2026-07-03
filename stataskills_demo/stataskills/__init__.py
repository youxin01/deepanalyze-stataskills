"""
StatABench statistical toolkit for code-execution agents.

The stable agent-facing interface is:

    from stataskills import run_tool, list_tools, tool_help
    result = run_tool("check_missing_values", data="data.csv", columns=["x"])

Functions can also be imported directly from this package.
"""

from __future__ import annotations

import inspect
import math
from pathlib import Path
from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd

from . import tools as _tools
from .tools import *  # noqa: F401,F403


TOOL_CATEGORIES: dict[str, str] = {
    "calculate_statistic": "eda",
    "check_missing_values": "eda",
    "detect_outliers": "eda",
    "check_column_type_is": "eda",
    "show_csv_info_en": "eda",
    "read_file": "io",
    "correlation_analysis": "correlation",
    "ci_normal": "confidence_interval",
    "ci_two_normal": "confidence_interval",
    "contingency_test": "hypothesis_test",
    "ks_test": "hypothesis_test",
    "mood_variance_test": "hypothesis_test",
    "nonparametric_test": "hypothesis_test",
    "fdr_control_df": "multiple_testing",
    "fwer_control_df": "multiple_testing",
    "simple_linear_regression": "regression",
    "multivariable_linear_regression": "regression",
    "run_glm": "regression",
    "huber_regression": "regression",
    "advanced_regression": "regression",
    "sparse_pca_analysis": "dimension_reduction",
    "test_stationarity": "time_series",
    "decompose_stl": "time_series",
    "auto_arima_modeling": "time_series",
    "kaplan_meier_plot": "survival",
    "logrank_test_compare": "survival",
    "fit_cox_model": "survival",
    "ab_ttest": "ab_test",
    "bootstrap_abtest": "ab_test",
    "ab_power_analysis": "ab_test",
    "bayesian_inference": "bayesian",
    "bayesian_linear_regression": "bayesian",
    "fit_hierarchical_model": "bayesian",
    "estimate_ATT_with_psm": "causal",
    "estimate_did_effect": "causal",
    "synthetic_control": "causal",
}

TOOL_NAMES = tuple(TOOL_CATEGORIES)

ALIASES: dict[str, str] = {
    "linear_regression": "simple_linear_regression",
    "ols": "simple_linear_regression",
    "missing_values": "check_missing_values",
    "outliers": "detect_outliers",
    "correlation": "correlation_analysis",
    "glm": "run_glm",
    "ttest": "ab_ttest",
    "ab_test": "ab_ttest",
    "read_csv": "read_csv",
    "load_csv": "read_csv",
    "describe": "describe",
    "summary": "describe",
}


def _tool(name: str):
    name = ALIASES.get(name, name)
    if name == "read_csv":
        return _read_csv
    if name == "describe":
        return _describe
    if name not in TOOL_CATEGORIES:
        available = ", ".join([*TOOL_NAMES, "read_csv", "load_csv", *ALIASES])
        raise KeyError(f"Unknown stataskills tool '{name}'. Available tools: {available}")
    return getattr(_tools, name)


def _canonical_name(name: str) -> str:
    return ALIASES.get(name, name)


def _read_csv(data: str | None = None, file_path: str | None = None, file: str | None = None) -> pd.DataFrame:
    path = data or file_path or file
    if not path:
        raise ValueError("read_csv requires `data`, `file_path`, or `file`.")
    return pd.read_csv(Path(path))


def _describe(
    data: str | pd.DataFrame | None = None,
    file_path: str | None = None,
    file: str | None = None,
    columns: list[str] | str | None = None,
) -> dict[str, dict[str, Any]]:
    source = data if data is not None else file_path or file
    if source is None:
        raise ValueError("describe requires `data`, `file_path`, or `file`.")
    df = pd.read_csv(source) if isinstance(source, str) else source.copy()
    if columns is not None:
        selected = [columns] if isinstance(columns, str) else columns
        df = df[selected]
    return df.describe(include="all").to_dict()


read_csv = _read_csv
describe = _describe


def _brief_doc(func: Any) -> str:
    doc = inspect.getdoc(func) or ""
    return doc.splitlines()[0] if doc else ""


def list_tools() -> list[dict[str, str]]:
    """Return available tool names, categories, signatures, and short descriptions."""
    items = []
    for name in TOOL_NAMES:
        func = _tool(name)
        items.append(
            {
                "name": name,
                "category": TOOL_CATEGORIES[name],
                "signature": f"{name}{inspect.signature(func)}",
                "description": _brief_doc(func),
            }
        )
    items.append(
        {
            "name": "read_csv",
            "category": "io",
            "signature": "read_csv(data: str | None = None, file_path: str | None = None, file: str | None = None) -> pandas.DataFrame",
            "description": "Read a CSV file into a pandas DataFrame for interactive code.",
        }
    )
    items.append(
        {
            "name": "describe",
            "category": "eda",
            "signature": "describe(data: str | pandas.DataFrame | None = None, file_path: str | None = None, file: str | None = None, columns: list[str] | str | None = None) -> dict",
            "description": "Return pandas describe() output for a CSV file or DataFrame.",
        }
    )
    return items


def tool_help(name: str) -> dict[str, str]:
    """Return signature and docstring for a tool."""
    canonical = _canonical_name(name)
    func = _tool(canonical)
    return {
        "name": canonical,
        "category": "io" if canonical == "read_csv" else ("eda" if canonical == "describe" else TOOL_CATEGORIES[canonical]),
        "signature": f"{name}{inspect.signature(func)}",
        "doc": inspect.getdoc(func) or "",
    }


def _json_safe(value: Any, *, max_rows: int = 20) -> Any:
    """Convert common scientific Python objects into printable Python data."""
    if isinstance(value, np.generic):
        return _json_safe(value.item(), max_rows=max_rows)
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else str(value)
    if isinstance(value, np.ndarray):
        return _json_safe(value.tolist(), max_rows=max_rows)
    if isinstance(value, pd.DataFrame):
        frame = value.head(max_rows)
        return {
            "type": "DataFrame",
            "shape": list(value.shape),
            "columns": [str(c) for c in value.columns],
            "head": frame.to_dict(orient="records"),
        }
    if isinstance(value, pd.Series):
        series = value.head(max_rows)
        return {
            "type": "Series",
            "name": str(value.name),
            "length": int(len(value)),
            "head": series.to_dict(),
        }
    if isinstance(value, Mapping):
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            if key in {"model", "trace"}:
                cleaned[str(key)] = _model_summary(item)
            else:
                cleaned[str(key)] = _json_safe(item, max_rows=max_rows)
        return cleaned
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item, max_rows=max_rows) for item in value]
    return _model_summary(value)


def _model_summary(value: Any) -> str:
    if hasattr(value, "summary"):
        try:
            summary = value.summary()
            if hasattr(summary, "as_text"):
                return summary.as_text()
            return str(summary)
        except Exception:
            pass
    return f"<{value.__class__.__module__}.{value.__class__.__name__}>"


def run_tool(name: str, /, **kwargs: Any) -> Any:
    """
    Run a statistical tool by name and return a JSON-safe result.

    Example:
        run_tool("check_missing_values", data="data.csv", columns=["income"])
    """
    canonical = _canonical_name(name)
    kwargs = _normalize_kwargs(canonical, kwargs)
    result = _tool(canonical)(**kwargs)
    if canonical == "read_csv":
        return result
    return _json_safe(result)


def _normalize_kwargs(name: str, kwargs: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(kwargs)
    if name == "read_file" and "file" in normalized and "file_path" not in normalized:
        normalized["file_path"] = normalized.pop("file")
    if "file" in normalized and "data" not in normalized:
        normalized["data"] = normalized.pop("file")
    if name == "calculate_statistic":
        if "statistic" in normalized and "method" not in normalized:
            normalized["method"] = normalized.pop("statistic")
        if "columns" in normalized and "column" not in normalized:
            columns = normalized.pop("columns")
            normalized["column"] = columns[0] if isinstance(columns, list) else columns
    if name == "correlation_analysis":
        normalized.setdefault("method", "pearson")
    if name == "simple_linear_regression":
        if "x" in normalized and "x_col" not in normalized:
            normalized["x_col"] = normalized.pop("x")
        if "y" in normalized and "y_col" not in normalized:
            normalized["y_col"] = normalized.pop("y")
    if name in {"multivariable_linear_regression", "run_glm", "huber_regression"}:
        if "X" in normalized and "data" not in normalized:
            x_data = normalized.pop("X")
            y_data = normalized.pop("y", None)
            if isinstance(x_data, pd.DataFrame) and y_data is not None:
                y_name = getattr(y_data, "name", None) or "target"
                normalized["data"] = x_data.copy()
                normalized["data"][y_name] = y_data
                normalized["y_col"] = y_name
                normalized["x_cols"] = list(x_data.columns)
        if "y" in normalized and "y_col" not in normalized:
            normalized["y_col"] = normalized.pop("y")
        if "x" in normalized and "x_cols" not in normalized:
            x_value = normalized.pop("x")
            normalized["x_cols"] = x_value if isinstance(x_value, list) else [x_value]
        for old_key in ("target", "dependent_var", "outcome", "response"):
            if old_key in normalized and "y_col" not in normalized:
                normalized["y_col"] = normalized.pop(old_key)
                break
        for old_key in ("predictors", "features", "independent_vars", "covariates"):
            if old_key in normalized and "x_cols" not in normalized:
                x_value = normalized.pop(old_key)
                normalized["x_cols"] = x_value if isinstance(x_value, list) else [x_value]
                break
    if name in {"test_stationarity", "decompose_stl", "auto_arima_modeling"}:
        if "series" in normalized and "data" not in normalized:
            series = normalized.pop("series")
            normalized["data"] = pd.DataFrame({"value": series})
            normalized.setdefault("column", "value")
    return normalized


__all__ = [
    "TOOL_CATEGORIES",
    "TOOL_NAMES",
    "list_tools",
    "tool_help",
    "run_tool",
    "read_csv",
    "describe",
    *TOOL_NAMES,
]
