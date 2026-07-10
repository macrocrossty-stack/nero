#!/usr/bin/env python3
"""仮立ち絵ジェネレータ — 影絵＋金の瞳スタイル。

本番立ち絵が入るまでのプレースホルダーを game/data/fgimage/ に生成する。
- yoru_normal.png / yoru_smile.png / yoru_battle.png : 執事ヨル（表情差分）
- yoru_panther.png : 黒豹

usage: python3 tools/make_placeholder_chara.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parent.parent / "game" / "data" / "fgimage"
BODY = (10, 10, 14, 255)
GOLD = (201, 168, 106, 255)


def butler(expr):
    W, H = 620, 1050
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = W // 2
    # 頭
    d.ellipse([cx - 78, 60, cx + 78, 250], fill=BODY)
    # 髪（少し流す）
    d.polygon([(cx - 82, 150), (cx - 96, 80), (cx - 30, 40), (cx + 60, 36), (cx + 96, 96), (cx + 82, 160)], fill=BODY)
    # 首・肩
    d.rectangle([cx - 30, 235, cx + 30, 285], fill=BODY)
    d.polygon([(cx - 150, 330), (cx - 40, 270), (cx + 40, 270), (cx + 150, 330)], fill=BODY)
    # 胴〜ロングコート
    d.polygon([(cx - 150, 330), (cx + 150, 330), (cx + 120, 660), (cx + 96, 1000), (cx - 96, 1000), (cx - 120, 660)], fill=BODY)
    # 腕
    d.polygon([(cx - 150, 335), (cx - 108, 335), (cx - 120, 640), (cx - 152, 636)], fill=BODY)
    d.polygon([(cx + 150, 335), (cx + 108, 335), (cx + 120, 640), (cx + 152, 636)], fill=BODY)
    # 白手袋の示唆
    d.ellipse([cx - 156, 620, cx - 116, 668], fill=(232, 228, 218, 230))
    d.ellipse([cx + 116, 620, cx + 156, 668], fill=(232, 228, 218, 230))
    # 襟のハイライト
    d.polygon([(cx - 26, 268), (cx, 300), (cx + 26, 268), (cx, 330)], fill=(232, 228, 218, 40))
    img = img.filter(ImageFilter.GaussianBlur(1.2))
    d = ImageDraw.Draw(img)
    # 目（表情差分）
    ey = 158
    if expr == "normal":
        d.rounded_rectangle([cx - 52, ey, cx - 16, ey + 12], 6, fill=GOLD)
        d.rounded_rectangle([cx + 16, ey, cx + 52, ey + 12], 6, fill=GOLD)
    elif expr == "smile":
        d.arc([cx - 54, ey - 6, cx - 14, ey + 22], 200, 340, fill=GOLD, width=8)
        d.arc([cx + 14, ey - 6, cx + 54, ey + 22], 200, 340, fill=GOLD, width=8)
    elif expr == "battle":
        d.polygon([(cx - 54, ey + 10), (cx - 16, ey - 2), (cx - 16, ey + 8), (cx - 52, ey + 18)], fill=GOLD)
        d.polygon([(cx + 54, ey + 10), (cx + 16, ey - 2), (cx + 16, ey + 8), (cx + 52, ey + 18)], fill=GOLD)
        # 剣
        d.line([(cx + 138, 650), (cx + 190, 990)], fill=(180, 184, 190, 220), width=7)
        d.line([(cx + 118, 682), (cx + 168, 664)], fill=(150, 130, 90, 255), width=9)
    d.text((10, H - 22), f"placeholder: yoru {expr}", fill=(140, 140, 140, 160))
    return img


def panther():
    W, H = 980, 640
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # 座り姿: 後躯
    d.ellipse([80, 260, 470, 600], fill=BODY)
    # 胸〜前躯
    d.polygon([(300, 590), (330, 300), (430, 190), (560, 180), (600, 320), (580, 590)], fill=BODY)
    # 前脚
    d.rectangle([400, 380, 470, 600], fill=BODY)
    d.rectangle([500, 380, 570, 600], fill=BODY)
    d.ellipse([390, 575, 485, 620], fill=BODY)
    d.ellipse([495, 575, 590, 620], fill=BODY)
    # 頭
    d.ellipse([430, 90, 640, 300], fill=BODY)
    # 耳
    d.polygon([(455, 120), (490, 40), (525, 110)], fill=BODY)
    d.polygon([(560, 105), (600, 38), (630, 118)], fill=BODY)
    # 尻尾
    d.arc([40, 380, 360, 700], 180, 330, fill=BODY, width=40)
    img = img.filter(ImageFilter.GaussianBlur(1.4))
    d = ImageDraw.Draw(img)
    # 金の瞳
    d.ellipse([485, 180, 525, 214], fill=GOLD)
    d.ellipse([565, 176, 605, 210], fill=GOLD)
    d.ellipse([498, 190, 510, 206], fill=(12, 12, 16, 255))
    d.ellipse([578, 186, 590, 202], fill=(12, 12, 16, 255))
    d.text((10, H - 22), "placeholder: yoru panther", fill=(140, 140, 140, 160))
    return img


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for e in ("normal", "smile", "battle"):
        butler(e).save(OUT / f"yoru_{e}.png")
        print("wrote", OUT / f"yoru_{e}.png")
    panther().save(OUT / "yoru_panther.png")
    print("wrote", OUT / "yoru_panther.png")
