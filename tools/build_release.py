#!/usr/bin/env python3
"""単一HTMLの配布ビルドを生成する。

preview/ のエンジン・シナリオ・素材（背景/立ち絵/音声）をすべて1ファイルに
インライン化する。プレビュー版と同じ player.js を使い、二重管理を避ける。

使い方:
    python3 tools/build_release.py            # 配布ビルド（手帳ロック・DEBUG_UNLOCK=false）
    python3 tools/build_release.py --preview  # 開発プレビュー（DEBUG_UNLOCK=true）
    python3 tools/build_release.py -o out.html # 出力先を指定

音声（game/data/bgm/*.m4a, game/data/se/*.m4a）は存在すれば base64 で埋め込む。
未配置でもエラーにならず、無音のビルドが出力される。
"""

import argparse
import base64
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def b64_dir(dir_path, patterns, mime):
    out = {}
    d = ROOT / dir_path
    if not d.is_dir():
        return out
    for pat in patterns:
        for f in sorted(d.glob(pat)):
            out[f.name] = f"data:{mime};base64," + base64.b64encode(f.read_bytes()).decode()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true",
                    help="開発プレビュー（DEBUG_UNLOCK=true・手帳全章解放）")
    ap.add_argument("-o", "--out", default=None, help="出力HTMLパス")
    args = ap.parse_args()

    debug_unlock = bool(args.preview)
    default_name = "nero-preview.html" if args.preview else "nero-release.html"
    out = Path(args.out) if args.out else (ROOT / "dist" / default_name)
    out.parent.mkdir(parents=True, exist_ok=True)

    scenarios = {f.name: f.read_text(encoding="utf-8")
                 for f in sorted((ROOT / "game/data/scenario").glob("*.ks"))}
    images = b64_dir("game/data/bgimage", ["*.jpg", "*.png"], "image/jpeg")
    charas = b64_dir("game/data/fgimage", ["*.png"], "image/png")
    bgm = b64_dir("game/data/bgm", ["*.m4a", "*.mp3", "*.ogg"], "audio/mp4")
    se = b64_dir("game/data/se", ["*.m4a", "*.mp3", "*.ogg", "*.wav"], "audio/mp4")

    player_js = (ROOT / "preview/player.js").read_text(encoding="utf-8")

    index_html = (ROOT / "preview/index.html").read_text(encoding="utf-8")
    style = index_html.split("<style>")[1].split("</style>")[0]
    stage = index_html.split('<div id="stage">')[1].split('</div>\n\n<script')[0]

    title = "眠り姫と黒豹の物語" + ("" if debug_unlock else "")
    sub = "— 開発プレビュー版 —" if debug_unlock else ""

    html = f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<style>{style}</style>
</head>
<body>
<div id="stage">{stage}</div>
<script>
window.SCENARIOS = {json.dumps(scenarios, ensure_ascii=False)};
window.BGDATA = {json.dumps(images)};
window.CHARADATA = {json.dumps(charas)};
window.BGMDATA = {json.dumps(bgm)};
window.SEDATA = {json.dumps(se)};
window.BG_RESOLVE = s => window.BGDATA[s] || "";
window.CHARA_RESOLVE = s => window.CHARADATA[s] || "";
window.BGM_RESOLVE = s => window.BGMDATA[s] || "";
window.SE_RESOLVE = s => window.SEDATA[s] || "";
window.DEBUG_UNLOCK = {str(debug_unlock).lower()};
</script>
<script>
{player_js}
</script>
</body>
</html>
"""

    out.write_text(html, encoding="utf-8")
    kind = "プレビュー(DEBUG_UNLOCK=true)" if debug_unlock else "配布(DEBUG_UNLOCK=false)"
    print(f"[{kind}] wrote {out} ({out.stat().st_size/1024:.0f} KB)")
    print(f"  scenarios={len(scenarios)} bg={len(images)} chara={len(charas)} "
          f"bgm={len(bgm)} se={len(se)}")


if __name__ == "__main__":
    main()
