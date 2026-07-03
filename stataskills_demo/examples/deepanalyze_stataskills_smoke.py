"""
Smoke test for using StatABench's stataskills package inside DeepAnalyze.

Run from any directory after installing the package into the DeepAnalyze
execution environment:

    conda run -n deepanalyze_app python examples/deepanalyze_stataskills_smoke.py
"""

from __future__ import annotations

from pathlib import Path

from stataskills import run_tool, tool_help


DATA_PATH = (
    Path("/nfsdata/zyx/statabench/skills-create/DeepAnalyze/API/example")
    / "Simpson.csv"
)


def main() -> None:
    print("tool_help(linear_regression):")
    print(tool_help("linear_regression")["signature"])

    df = run_tool("read_csv", file=str(DATA_PATH))
    print("rows, cols:", df.shape)

    print("income describe:")
    print(run_tool("describe", data=df, columns=["income"])["income"])

    print("missing values:")
    print(run_tool("check_missing_values", data=df, columns=["income", "success"]))

    print("linear regression:")
    result = run_tool("linear_regression", data=df, x="income", y="success")
    print({key: result[key] for key in ["intercept", "coefficient", "r_squared"]})


if __name__ == "__main__":
    main()
