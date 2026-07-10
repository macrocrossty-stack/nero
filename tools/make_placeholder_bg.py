#!/usr/bin/env python3
"""仮背景ジェネレータ — 『眠り姫と黒豹の物語』

本番素材が揃うまでの仮背景 (1280x720 JPEG) を game/data/bgimage/ に生成する。
各シーンのカラースクリプト（docs/03_素材リスト.md）に合わせた
グラデーション＋シルエット＋ビネットの簡易画像。

usage: python3 tools/make_placeholder_bg.py
requires: pip install pillow
"""

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

W, H = 1280, 720
OUT = Path(__file__).resolve().parent.parent / "game" / "data" / "bgimage"


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def vgrad(top, bottom):
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        d.line([(0, y), (W, y)], fill=lerp(top, bottom, y / H))
    return img


def vignette(img, strength=0.55):
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    d.ellipse([-W * 0.25, -H * 0.35, W * 1.25, H * 1.35], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(160))
    black = Image.new("RGB", (W, H), (0, 0, 0))
    return Image.composite(img, Image.blend(img, black, strength), mask)


def grain(img, amount=8):
    rnd = random.Random(7)
    px = img.load()
    for _ in range(W * H // 14):
        x, y = rnd.randrange(W), rnd.randrange(H)
        r, g, b = px[x, y]
        n = rnd.randint(-amount, amount)
        px[x, y] = (max(0, min(255, r + n)), max(0, min(255, g + n)), max(0, min(255, b + n)))
    return img


def trees(d, color, seed=1, density=26, y_base=H):
    rnd = random.Random(seed)
    for _ in range(density):
        x = rnd.randrange(-40, W + 40)
        w = rnd.randint(18, 60)
        h = rnd.randint(int(H * 0.45), int(H * 1.0))
        d.polygon([(x - w // 2, y_base), (x + w // 2, y_base), (x + w // 6, y_base - h), (x - w // 6, y_base - h)], fill=color)
        for _ in range(5):
            bx = x + rnd.randint(-w, w)
            by = y_base - h + rnd.randint(0, h // 3)
            d.ellipse([bx - 70, by - 40, bx + 70, by + 40], fill=color)


def moon(img, cx, cy, r, color=(225, 228, 210)):
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([cx - r * 3, cy - r * 3, cx + r * 3, cy + r * 3], fill=(40, 48, 60))
    glow = glow.filter(ImageFilter.GaussianBlur(60))
    img = Image.blend(img, Image.composite(glow, Image.new("RGB", (W, H), (0, 0, 0)), Image.new("L", (W, H), 255)), 0.0)
    base = img.copy()
    d = ImageDraw.Draw(base)
    d.ellipse([cx - r * 2.2, cy - r * 2.2, cx + r * 2.2, cy + r * 2.2], fill=lerp((0, 0, 0), color, 0.18))
    base = base.filter(ImageFilter.GaussianBlur(30))
    out = Image.blend(img, base, 0.6)
    d = ImageDraw.Draw(out)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    return out


def stars(d, seed=3, n=140, ymax=int(H * 0.7)):
    rnd = random.Random(seed)
    for _ in range(n):
        x, y = rnd.randrange(W), rnd.randrange(ymax)
        v = rnd.randint(120, 235)
        d.point((x, y), fill=(v, v, min(255, v + 15)))


def label(img, text):
    d = ImageDraw.Draw(img)
    d.text((14, H - 24), f"placeholder: {text}", fill=(140, 140, 140))
    return img


def save(img, name, text):
    OUT.mkdir(parents=True, exist_ok=True)
    img = grain(vignette(img))
    img = label(img, text)
    img.save(OUT / name, quality=88)
    print("wrote", OUT / name)


def bg_black():
    save(Image.new("RGB", (W, H), (2, 2, 4)), "bg_black.jpg", "black")


def bg_storybook():
    img = vgrad((72, 58, 40), (38, 28, 18))
    d = ImageDraw.Draw(img)
    # 開いた絵本のページ
    d.rounded_rectangle([120, 90, W // 2 - 6, H - 90], 8, fill=(214, 197, 158))
    d.rounded_rectangle([W // 2 + 6, 90, W - 120, H - 90], 8, fill=(222, 206, 168))
    d.line([(W // 2, 90), (W // 2, H - 90)], fill=(90, 74, 50), width=6)
    for x0 in (170, W // 2 + 56):
        for i in range(9):
            y = 160 + i * 44
            d.line([(x0, y), (x0 + 420, y)], fill=(150, 132, 100), width=3)
    save(img, "bg_storybook.jpg", "storybook")


def bg_forest_night():
    img = vgrad((10, 18, 38), (3, 6, 12))
    d = ImageDraw.Draw(img)
    stars(d)
    img = moon(img, 950, 150, 52)
    d = ImageDraw.Draw(img)
    trees(d, (5, 9, 16), seed=11)
    trees(d, (2, 4, 8), seed=22, density=18)
    save(img, "bg_forest_night.jpg", "forest night")


def bg_forest_dawn():
    img = vgrad((120, 110, 90), (190, 150, 96))
    d = ImageDraw.Draw(img)
    d.ellipse([W * 0.4, H * 0.35, W * 0.6, H * 0.62], fill=(235, 210, 150))
    img = img.filter(ImageFilter.GaussianBlur(24))
    d = ImageDraw.Draw(img)
    trees(d, (70, 66, 58), seed=31)
    trees(d, (44, 42, 38), seed=42, density=16)
    # 霧
    fog = Image.new("RGB", (W, H), (0, 0, 0))
    fd = ImageDraw.Draw(fog)
    for i in range(4):
        y = int(H * 0.55) + i * 40
        fd.ellipse([-200, y, W + 200, y + 140], fill=(210, 195, 165))
    fog = fog.filter(ImageFilter.GaussianBlur(50))
    img = Image.blend(img, Image.composite(fog, img, Image.new("L", (W, H), 110)), 0.45)
    save(img, "bg_forest_dawn.jpg", "forest dawn")


def bg_mansion_ext():
    img = vgrad((150, 140, 122), (96, 92, 82))
    d = ImageDraw.Draw(img)
    trees(d, (60, 62, 52), seed=51, density=14)
    # 屋敷シルエット
    d.rectangle([340, 250, 940, 640], fill=(52, 48, 46))
    d.polygon([(320, 250), (960, 250), (640, 130)], fill=(40, 36, 34))
    d.rectangle([560, 210, 720, 640], fill=(58, 53, 50))
    d.polygon([(540, 210), (740, 210), (640, 110)], fill=(44, 40, 38))
    for gx in range(5):
        for gy in range(3):
            x = 380 + gx * 120
            y = 300 + gy * 110
            d.rectangle([x, y, x + 42, y + 66], fill=(158, 148, 110))
    d.rectangle([610, 500, 670, 640], fill=(30, 26, 24))  # 扉
    save(img, "bg_mansion_ext.jpg", "mansion exterior")


def bg_mansion_hall():
    img = vgrad((44, 38, 34), (16, 13, 12))
    d = ImageDraw.Draw(img)
    # 奥の窓と光
    for i, x in enumerate((180, 520, 860)):
        d.rounded_rectangle([x, 120, x + 160, 430], 80, fill=(96, 92, 76))
        d.rounded_rectangle([x + 16, 140, x + 144, 414], 64, fill=(60, 58, 48))
    beam = Image.new("RGB", (W, H), (0, 0, 0))
    bd = ImageDraw.Draw(beam)
    bd.polygon([(560, 130), (720, 130), (900, 700), (420, 700)], fill=(70, 66, 50))
    beam = beam.filter(ImageFilter.GaussianBlur(70))
    img = Image.blend(img, Image.composite(beam, img, Image.new("L", (W, H), 120)), 0.4)
    d = ImageDraw.Draw(img)
    # シャンデリア
    d.line([(640, 0), (640, 120)], fill=(20, 18, 16), width=5)
    d.ellipse([560, 110, 720, 170], outline=(90, 80, 55), width=6)
    # 床
    d.rectangle([0, 560, W, H], fill=(28, 23, 20))
    for i in range(9):
        d.line([(i * 160 - 120, H), (i * 160 + 80, 560)], fill=(20, 16, 14), width=3)
    save(img, "bg_mansion_hall.jpg", "mansion hall")


def bg_library():
    img = vgrad((36, 32, 26), (14, 12, 10))
    d = ImageDraw.Draw(img)
    rnd = random.Random(5)
    # 本棚
    for sx in (60, 460, 860):
        d.rectangle([sx, 60, sx + 360, 620], fill=(45, 34, 24))
        for row in range(6):
            y = 90 + row * 88
            d.rectangle([sx + 12, y, sx + 348, y + 70], fill=(24, 18, 13))
            x = sx + 16
            while x < sx + 330:
                bw = rnd.randint(12, 30)
                bh = rnd.randint(50, 66)
                col = rnd.choice([(96, 60, 44), (60, 76, 66), (110, 92, 56), (70, 50, 66), (90, 78, 64)])
                d.rectangle([x, y + 70 - bh, x + bw, y + 70], fill=col)
                x += bw + 3
    # 緑のランプの光
    lamp = Image.new("RGB", (W, H), (0, 0, 0))
    ld = ImageDraw.Draw(lamp)
    ld.ellipse([500, 380, 800, 620], fill=(40, 70, 40))
    lamp = lamp.filter(ImageFilter.GaussianBlur(80))
    img = Image.blend(img, Image.composite(lamp, img, Image.new("L", (W, H), 150)), 0.5)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 620, W, H], fill=(22, 17, 13))
    save(img, "bg_library.jpg", "library")


def bg_bedroom():
    img = vgrad((88, 82, 92), (40, 36, 44))
    d = ImageDraw.Draw(img)
    # 窓とカーテン
    d.rounded_rectangle([880, 100, 1150, 480], 20, fill=(150, 148, 130))
    d.rectangle([850, 80, 900, 500], fill=(180, 176, 168))
    d.rectangle([1130, 80, 1180, 500], fill=(180, 176, 168))
    # 天蓋ベッド
    d.rectangle([160, 180, 200, 620], fill=(70, 58, 52))
    d.rectangle([620, 180, 660, 620], fill=(70, 58, 52))
    d.rectangle([140, 160, 680, 200], fill=(80, 66, 58))
    d.polygon([(200, 200), (320, 200), (240, 560)], fill=(205, 200, 195))
    d.polygon([(620, 200), (500, 200), (580, 560)], fill=(198, 193, 188))
    d.rectangle([180, 480, 640, 620], fill=(190, 184, 178))
    d.rectangle([180, 450, 640, 500], fill=(210, 205, 200))
    img = img.filter(ImageFilter.GaussianBlur(1))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 620, W, H], fill=(34, 28, 30))
    save(img, "bg_bedroom.jpg", "bedroom")


def bg_garden():
    img = vgrad((140, 150, 130), (70, 90, 66))
    d = ImageDraw.Draw(img)
    trees(d, (52, 66, 48), seed=61, density=10)
    # 石壁と野薔薇
    d.rectangle([0, 340, W, 470], fill=(110, 104, 92))
    rnd = random.Random(9)
    for _ in range(90):
        x, y = rnd.randrange(W), rnd.randrange(330, 480)
        d.ellipse([x, y, x + 14, y + 14], fill=(70, 96, 60))
    for _ in range(36):
        x, y = rnd.randrange(W), rnd.randrange(335, 475)
        d.ellipse([x, y, x + 9, y + 9], fill=(190, 120, 130))
    # 噴水跡
    d.ellipse([440, 520, 840, 660], fill=(120, 116, 104))
    d.ellipse([480, 535, 800, 645], fill=(88, 96, 88))
    d.rectangle([620, 430, 660, 560], fill=(120, 116, 104))
    d.rectangle([0, 640, W, H], fill=(64, 80, 58))
    save(img, "bg_garden.jpg", "garden")


def bg_sky_corrupt():
    img = vgrad((70, 74, 84), (120, 112, 100))
    rnd = random.Random(13)
    oil = Image.new("RGB", (W, H), (0, 0, 0))
    od = ImageDraw.Draw(oil)
    cols = [(90, 40, 90), (40, 80, 90), (110, 90, 30), (60, 30, 70), (30, 60, 50)]
    for _ in range(26):
        x, y = rnd.randrange(W), rnd.randrange(int(H * 0.75))
        rx, ry = rnd.randint(80, 320), rnd.randint(30, 110)
        od.ellipse([x - rx, y - ry, x + rx, y + ry], fill=rnd.choice(cols))
    oil = oil.filter(ImageFilter.GaussianBlur(40))
    img = Image.blend(img, Image.composite(oil, img, Image.new("L", (W, H), 140)), 0.55)
    d = ImageDraw.Draw(img)
    trees(d, (40, 44, 40), seed=71, density=12)
    save(img, "bg_sky_corrupt.jpg", "corrupted sky")


def bg_servant_room():
    img = vgrad((70, 66, 62), (34, 31, 29))
    d = ImageDraw.Draw(img)
    # 小さな窓と窓辺の椅子
    d.rounded_rectangle([880, 120, 1120, 420], 14, fill=(140, 138, 122))
    d.rectangle([985, 120, 1015, 420], fill=(90, 86, 76))
    d.rectangle([880, 260, 1120, 280], fill=(90, 86, 76))
    d.rectangle([900, 430, 1010, 600], fill=(58, 48, 40))  # 椅子
    d.rectangle([900, 430, 920, 600], fill=(48, 40, 34))
    # 質素な寝台と机
    d.rectangle([120, 420, 520, 620], fill=(96, 92, 86))
    d.rectangle([120, 380, 520, 430], fill=(120, 116, 108))
    d.rectangle([120, 300, 160, 620], fill=(64, 54, 46))
    d.rectangle([600, 400, 820, 620], fill=(66, 56, 46))  # 机
    d.rectangle([620, 420, 800, 440], fill=(52, 44, 38))
    img = img.filter(ImageFilter.GaussianBlur(1))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 620, W, H], fill=(40, 34, 30))
    save(img, "bg_servant_room.jpg", "servant room")


def bg_corridor():
    img = vgrad((52, 46, 40), (20, 17, 15))
    d = ImageDraw.Draw(img)
    # 奥へ続く廊下と肖像画の列（顔は褪せて描かない）
    d.polygon([(0, H), (W, H), (W * 0.68, H * 0.62), (W * 0.32, H * 0.62)], fill=(58, 48, 40))
    for i in range(4):
        x = 90 + i * 260
        w = 170 - i * 18
        y = 110 + i * 34
        h = 260 - i * 32
        d.rectangle([x, y, x + w, y + h], fill=(96, 78, 40))
        d.rectangle([x + 12, y + 12, x + w - 12, y + h - 12], fill=(44, 38, 32))
        # 人物のシルエット（顔の位置だけ靄のように明るい）
        cx = x + w // 2
        d.polygon([(cx - w // 4, y + h - 14), (cx + w // 4, y + h - 14), (cx + w // 6, y + h // 2), (cx - w // 6, y + h // 2)], fill=(30, 26, 24))
        d.ellipse([cx - 22, y + 34, cx + 22, y + 88], fill=(120, 112, 100))
    beam = Image.new("RGB", (W, H), (0, 0, 0))
    bd = ImageDraw.Draw(beam)
    bd.polygon([(W, 60), (W, 320), (W * 0.5, H)], fill=(60, 54, 40))
    beam = beam.filter(ImageFilter.GaussianBlur(80))
    img = Image.blend(img, Image.composite(beam, img, Image.new("L", (W, H), 120)), 0.35)
    save(img, "bg_corridor.jpg", "portrait corridor")


def bg_attic():
    img = vgrad((44, 38, 32), (18, 15, 13))
    d = ImageDraw.Draw(img)
    # 屋根の梁
    d.polygon([(0, 260), (W // 2, 30), (W, 260), (W, 200), (W // 2, 0), (0, 200)], fill=(30, 24, 20))
    for x0 in (200, 520, 840, 1140):
        d.line([(x0, H * 0.1), (x0 - 140, H)], fill=(36, 29, 24), width=26)
    # まるい窓と月光
    d.ellipse([560, 90, 720, 250], fill=(150, 158, 150))
    d.ellipse([580, 110, 700, 230], fill=(196, 204, 196))
    beam = Image.new("RGB", (W, H), (0, 0, 0))
    bd = ImageDraw.Draw(beam)
    bd.polygon([(580, 120), (700, 120), (860, 700), (420, 700)], fill=(70, 76, 70))
    beam = beam.filter(ImageFilter.GaussianBlur(70))
    img = Image.blend(img, Image.composite(beam, img, Image.new("L", (W, H), 130)), 0.45)
    d = ImageDraw.Draw(img)
    # 衣裳箱とがらくた
    d.rectangle([460, 480, 820, 650], fill=(74, 56, 38))
    d.rectangle([460, 460, 820, 500], fill=(90, 70, 48))
    d.rectangle([470, 545, 810, 560], fill=(52, 40, 28))
    d.ellipse([150, 470, 300, 640], outline=(60, 50, 42), width=8)   # 鳥かご
    d.line([(225, 470), (225, 430)], fill=(60, 50, 42), width=6)
    d.polygon([(960, 640), (1060, 640), (1040, 500), (980, 500)], fill=(56, 46, 40))  # 椅子
    d.rectangle([0, 640, W, H], fill=(30, 24, 20))
    save(img, "bg_attic.jpg", "attic")


if __name__ == "__main__":
    bg_black()
    bg_storybook()
    bg_forest_night()
    bg_forest_dawn()
    bg_mansion_ext()
    bg_mansion_hall()
    bg_library()
    bg_bedroom()
    bg_garden()
    bg_sky_corrupt()
    bg_servant_room()
    bg_corridor()
    bg_attic()
    print("done.")
