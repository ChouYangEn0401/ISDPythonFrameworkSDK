This folder contains pytest-based file-format tests that compare a baseline file named with the pattern

- `[BU] sample.<ext>` in `tests/test_file/expected/`
- `sample.<ext>` in `tests/test_file/target/`

Run the sample generator first, then copy `tests/test_file/base` to `expected` and `target`, edit files under `target` to simulate changes, then run:

```bash
python -m pytest tests/file_test -q
```

Tests will skip formats whose parser libraries are not installed (e.g., `openpyxl`, `pyyaml`, `tomli`).
