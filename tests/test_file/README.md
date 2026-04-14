tests/test_file — quick guide

This folder contains a small generator to create sample files you can use to test the comparison tools.

1) Generate base sample files

```bash
python tests/test_file/generate_samples.py
```

This will create `tests/test_file/base/` with sample files for: csv, json, jsonl, txt, yaml, xml, ini, toml, xlsx (if `openpyxl` installed).

2) Create `expected` and `target` test sets

- Copy the base folder to create your bench (expected) and target sets:

```bash
# Windows PowerShell
Copy-Item -Recurse tests/test_file/base tests/test_file/expected
Copy-Item -Recurse tests/test_file/base tests/test_file/target
```

3) Modify files under `tests/test_file/target` to simulate regressions or intentional changes.

4) Create a `suite.yaml` or `suite.json` describing tests (see project README for sample config) and run the runner:

```bash
python tools/run_file_tests.py suite.yaml --html report.html
```

The report will fail (exit code 1) if any difference is detected.

If you want, I can also pre-generate `expected` and `target` pairs where `target` includes a few deliberate changes — tell me and I'll generate them.