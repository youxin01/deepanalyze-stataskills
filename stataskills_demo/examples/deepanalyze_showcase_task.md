# Run the stataskills Showcase Driver

Use the uploaded files. Your next response must execute the uploaded driver
script. Do not inspect for pre-existing output files first, and do not rewrite
the statistical workflow manually.

Return exactly one executable code block first:

```python
exec(open("deepanalyze_showcase_driver.py", encoding="utf-8").read())
```

After the code executes, summarize the generated
`stataskills_showcase_report.md` and explicitly mention that the audit lines
starting with `STATASKILLS_CALL:` prove where `stataskills.run_tool()` was used.
