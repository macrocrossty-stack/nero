#!/usr/bin/env python3
"""シナリオ(.ks)を preview/scenario_data.js に埋め込む。

ブラウザの file:// では fetch が使えないため、シナリオを JS として
スナップショットしておく方式。シナリオを書き換えたら再実行すること。

usage: python3 tools/build_preview.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCENARIO_DIR = ROOT / "game" / "data" / "scenario"
OUT = ROOT / "preview" / "scenario_data.js"

data = {}
for f in sorted(SCENARIO_DIR.glob("*.ks")):
    data[f.name] = f.read_text(encoding="utf-8")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(
    "// 自動生成: python3 tools/build_preview.py で再生成\n"
    "window.SCENARIOS = " + json.dumps(data, ensure_ascii=False) + ";\n",
    encoding="utf-8",
)
print("wrote", OUT, f"({len(data)} files)")
