"""Generate a set of sample files for file-comparison testing.

This script writes a small collection of sample files to `tests/test_file/base/`.
Run it, then copy the files to create your two versions:
  - keep one copy as `expected/` (bench)
  - modify the other and place into `target/`

Example:
  python tests/test_file/generate_samples.py
  cp -r tests/test_file/base tests/test_file/expected
  cp -r tests/test_file/base tests/test_file/target
  # then edit files under tests/test_file/target to simulate changes

The script creates: csv, json, jsonl, txt, yaml, xml, ini, toml, xlsx
"""
import os
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "base"
OUT.mkdir(parents=True, exist_ok=True)

# CSV
import csv
with open(OUT / "sample.csv", "w", newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(["id","name","score"]) 
    w.writerow([1, "Alice", 95.5])
    w.writerow([2, "Bob", 88.0])

# JSON
data = {"meta": {"generated_by": "generator", "version": 1}, "items": [{"id":1,"v":10},{"id":2,"v":20}]}
with open(OUT / "sample.json", "w", encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

# JSONL
with open(OUT / "sample.jsonl", "w", encoding='utf-8') as f:
    for obj in data['items']:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

# TXT
with open(OUT / "sample.txt", "w", encoding='utf-8') as f:
    f.write("line one\nline TWO\nlast line\n")

# YAML
try:
    import yaml
    with open(OUT / "sample.yaml", "w", encoding='utf-8') as f:
        yaml.safe_dump(data, f, allow_unicode=True)
except Exception:
    # skip if pyyaml not installed
    with open(OUT / "sample.yaml", "w", encoding='utf-8') as f:
        f.write("# pyyaml not installed; sample YAML placeholder\nmeta: {generated_by: generator}\n")

# XML (simple)
import xml.etree.ElementTree as ET
root = ET.Element('root')
meta = ET.SubElement(root, 'meta')
ET.SubElement(meta, 'generated_by').text = 'generator'
items = ET.SubElement(root, 'items')
for it in data['items']:
    e = ET.SubElement(items, 'item')
    ET.SubElement(e, 'id').text = str(it['id'])
    ET.SubElement(e, 'v').text = str(it['v'])
ET.ElementTree(root).write(OUT / 'sample.xml', encoding='utf-8', xml_declaration=True)

# INI
import configparser
cfg = configparser.ConfigParser()
cfg['server'] = {'host': 'localhost', 'port': '8080'}
cfg['meta'] = {'version': '1'}
with open(OUT / 'sample.ini', 'w', encoding='utf-8') as f:
    cfg.write(f)

# TOML (py311: tomllib read-only; write as plain text)
try:
    import tomllib  # only for reading, so write a sample string
    toml_text = '[meta]\nname = "sample"\n[items]\ncount = 2\n'
    with open(OUT / 'sample.toml', 'w', encoding='utf-8') as f:
        f.write(toml_text)
except Exception:
    with open(OUT / 'sample.toml', 'w', encoding='utf-8') as f:
        f.write('# toml sample\nname = "sample"\n')

# XLSX
try:
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = 'Sheet'
    ws.append(['id', 'name', 'score'])
    ws.append([1, 'Alice', 95.5])
    ws.append([2, 'Bob', 88.0])
    wb.save(OUT / 'sample.xlsx')
except Exception:
    with open(OUT / 'sample.xlsx.txt', 'w', encoding='utf-8') as f:
        f.write('openpyxl not installed; no xlsx generated')

print(f'Generated sample files under: {OUT}')
print('Next: copy the `base` folder to `expected` and `target`, then modify `target` to simulate changes.')
