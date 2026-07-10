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



def bg_road():
    img = vgrad((170, 176, 168), (120, 132, 110))
    d = ImageDraw.Draw(img)
    # 遠景の丘
    d.ellipse([-300, 300, 700, 700], fill=(104, 120, 92))
    d.ellipse([500, 320, 1600, 760], fill=(96, 112, 86))
    # 草原
    d.rectangle([0, 430, W, H], fill=(110, 128, 94))
    # 街道（奥へ細くなる）
    d.polygon([(W * 0.44, 430), (W * 0.5, 430), (W * 0.82, H), (W * 0.28, H)], fill=(150, 134, 104))
    d.polygon([(W * 0.465, 430), (W * 0.478, 430), (W * 0.56, H), (W * 0.5, H)], fill=(132, 118, 92))
    trees(d, (78, 96, 70), seed=81, density=7)
    img = img.filter(ImageFilter.GaussianBlur(1))
    save(img, "bg_road.jpg", "road")


def bg_village():
    img = vgrad((188, 172, 140), (140, 120, 92))
    d = ImageDraw.Draw(img)
    # 家並み
    rnd = random.Random(17)
    for i, x in enumerate((30, 300, 590, 880, 1120)):
        w = rnd.randint(180, 250)
        h = rnd.randint(180, 260)
        base = 500
        col = rnd.choice([(150, 128, 100), (162, 140, 112), (140, 118, 92)])
        d.rectangle([x, base - h, x + w, base], fill=col)
        d.polygon([(x - 16, base - h), (x + w + 16, base - h), (x + w // 2, base - h - rnd.randint(70, 110))], fill=(96, 72, 56))
        # 窓
        for wx in range(x + 24, x + w - 30, 60):
            d.rectangle([wx, base - h + 50, wx + 30, base - h + 95], fill=(226, 196, 130))
    # 広場
    d.rectangle([0, 500, W, H], fill=(168, 148, 116))
    for i in range(24):
        y = 520 + i * 9
        d.line([(0, y), (W, y)], fill=(158, 138, 108), width=3)
    # 井戸
    d.ellipse([560, 560, 740, 660], fill=(120, 110, 96))
    d.rectangle([580, 470, 600, 590], fill=(96, 78, 60))
    d.rectangle([700, 470, 720, 590], fill=(96, 78, 60))
    d.polygon([(560, 480), (740, 480), (650, 420)], fill=(104, 80, 60))
    save(img, "bg_village.jpg", "village")


def bg_lake_night():
    # 上半分: 星空 / 下半分: 湖面（星の鏡映）— 第4章の見せ場
    img = vgrad((8, 14, 34), (16, 26, 52))
    d = ImageDraw.Draw(img)
    horizon = int(H * 0.56)
    rnd = random.Random(23)
    # 空の星
    for _ in range(220):
        x, y = rnd.randrange(W), rnd.randrange(horizon)
        v = rnd.randint(140, 255)
        d.point((x, y), fill=(v, v, min(255, v + 12)))
        if rnd.random() < 0.06:
            d.ellipse([x - 1, y - 1, x + 1, y + 1], fill=(v, v, 255))
    img = moon(img, 240, 110, 40)
    d = ImageDraw.Draw(img)
    # 湖面
    d.rectangle([0, horizon, W, H], fill=(10, 18, 40))
    for yy in range(horizon, H, 3):
        t = (yy - horizon) / (H - horizon)
        d.line([(0, yy), (W, yy)], fill=lerp((12, 22, 48), (5, 9, 22), t))
    # 鏡映の星（縦ににじむ）
    for _ in range(160):
        x = rnd.randrange(W)
        y = rnd.randrange(horizon + 8, H - 10)
        v = rnd.randint(90, 200)
        d.line([(x, y), (x, y + rnd.randint(2, 6))], fill=(v, v, min(255, v + 20)))
    # 月の鏡映
    for i in range(14):
        yy = horizon + 24 + i * 22
        wgt = max(4, 46 - i * 3)
        d.line([(240 - wgt, yy), (240 + wgt, yy)], fill=(120, 124, 116), width=2)
    # 対岸と手前の岸
    d.ellipse([-200, horizon - 36, 420, horizon + 30], fill=(6, 10, 20))
    d.ellipse([900, horizon - 26, 1500, horizon + 26], fill=(6, 10, 20))
    d.polygon([(0, H), (W * 0.3, H), (W * 0.12, H - 60), (0, H - 90)], fill=(8, 10, 18))
    # 焚き火のあかり（画面左下）
    fire = Image.new("RGB", (W, H), (0, 0, 0))
    fd = ImageDraw.Draw(fire)
    fd.ellipse([60, H - 160, 260, H - 40], fill=(140, 80, 30))
    fire = fire.filter(ImageFilter.GaussianBlur(60))
    img = Image.blend(img, Image.composite(fire, img, Image.new("L", (W, H), 130)), 0.5)
    save(img, "bg_lake_night.jpg", "lake night")



def bg_cliff_door():
    img = vgrad((60, 66, 74), (28, 30, 34))
    d = ImageDraw.Draw(img)
    # 崖の岩肌
    rnd = random.Random(29)
    d.rectangle([0, 0, W, H], fill=(52, 54, 58))
    for _ in range(140):
        x, y = rnd.randrange(W), rnd.randrange(H)
        w, h = rnd.randint(40, 180), rnd.randint(16, 60)
        c = rnd.choice([(46, 48, 52), (58, 60, 64), (40, 42, 46)])
        d.polygon([(x, y), (x + w, y + rnd.randint(-10, 10)), (x + w - 20, y + h), (x - 10, y + h - 6)], fill=c)
    # 苔と蔦
    for _ in range(60):
        x, y = rnd.randrange(W), rnd.randrange(H)
        d.ellipse([x, y, x + rnd.randint(10, 40), y + rnd.randint(6, 18)], fill=(44, 60, 44))
    # アーチの扉
    d.rounded_rectangle([500, 200, 780, 700], 140, fill=(24, 22, 26))
    d.rounded_rectangle([516, 216, 764, 700], 124, fill=(34, 30, 36))
    # 扉の紋様: 中心の星と七つの輪（星の部屋の予告）
    cx, cy = 640, 400
    d.ellipse([cx - 7, cy - 7, cx + 7, cy + 7], fill=(150, 132, 96))
    import math as _m
    for k in range(7):
        a = _m.pi * 2 * k / 7 - _m.pi / 2
        px, py = cx + int(_m.cos(a) * 60), cy + int(_m.sin(a) * 60)
        d.ellipse([px - 4, py - 4, px + 4, py + 4], fill=(120, 106, 80))
    d.ellipse([cx - 60, cy - 60, cx + 60, cy + 60], outline=(90, 80, 62), width=3)
    save(img, "bg_cliff_door.jpg", "cliff door")


def bg_cathedral():
    img = vgrad((30, 28, 36), (12, 11, 15))
    d = ImageDraw.Draw(img)
    # パイプオルガン風の柱（調律塔の心臓）
    for i in range(11):
        x = 140 + i * 92
        h = 380 + (i % 2) * 60 + abs(5 - i) * -18
        d.rounded_rectangle([x, 520 - h, x + 54, 520], 26, fill=(58, 52, 66))
        d.rounded_rectangle([x + 8, 520 - h + 14, x + 24, 520], 10, fill=(78, 70, 86))
    # 薔薇窓（星図モチーフ）
    cx, cy, r = 640, 170, 110
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(40, 44, 60))
    d.ellipse([cx - r + 10, cy - r + 10, cx + r - 10, cy + r - 10], fill=(66, 74, 96))
    import math as _m
    for k in range(7):
        a = _m.pi * 2 * k / 7 - _m.pi / 2
        px, py = cx + int(_m.cos(a) * 62), cy + int(_m.sin(a) * 62)
        d.ellipse([px - 14, py - 14, px + 14, py + 14], fill=(120, 126, 150))
    d.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], fill=(190, 178, 140))
    # 光の帯
    beam = Image.new("RGB", (W, H), (0, 0, 0))
    bd = ImageDraw.Draw(beam)
    bd.polygon([(cx - 60, cy), (cx + 60, cy), (cx + 220, H), (cx - 220, H)], fill=(56, 58, 72))
    beam = beam.filter(ImageFilter.GaussianBlur(60))
    img = Image.blend(img, Image.composite(beam, img, Image.new("L", (W, H), 130)), 0.45)
    d = ImageDraw.Draw(img)
    # 床と祭壇
    d.rectangle([0, 520, W, H], fill=(26, 23, 28))
    for i in range(10):
        d.line([(i * 150 - 100, H), (i * 150 + 100, 520)], fill=(20, 17, 21), width=2)
    d.rounded_rectangle([540, 470, 740, 560], 8, fill=(48, 42, 50))
    save(img, "bg_cathedral.jpg", "cathedral")


def bg_star_room():
    # 星の部屋: 彼女が生まれたプラネタリウム。中心の星と七つの輪＝湖の星図と同じ
    img = Image.new("RGB", (W, H), (6, 8, 18))
    d = ImageDraw.Draw(img)
    rnd = random.Random(37)
    # ドームの星々
    for _ in range(400):
        x, y = rnd.randrange(W), rnd.randrange(H)
        v = rnd.randint(70, 220)
        d.point((x, y), fill=(v, v, min(255, v + 25)))
    # 渦巻き
    import math as _m
    cx, cy = 640, 300
    for t in range(0, 720, 4):
        a = _m.radians(t)
        rr = 30 + t * 0.55
        x, y = cx + _m.cos(a + 2) * rr, cy + _m.sin(a + 2) * rr * 0.6
        v = max(90, 230 - t // 5)
        d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(v, v, min(255, v + 20)))
    # 中心の星
    d.ellipse([cx - 16, cy - 16, cx + 16, cy + 16], fill=(240, 232, 200))
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([cx - 90, cy - 90, cx + 90, cy + 90], fill=(120, 110, 70))
    glow = glow.filter(ImageFilter.GaussianBlur(50))
    img = Image.blend(img, Image.composite(glow, img, Image.new("L", (W, H), 150)), 0.5)
    d = ImageDraw.Draw(img)
    # 七つの輪の星
    for k in range(7):
        a = _m.pi * 2 * k / 7 - _m.pi / 2
        px, py = cx + int(_m.cos(a) * 190), cy + int(_m.sin(a) * 120)
        d.ellipse([px - 7, py - 7, px + 7, py + 7], fill=(220, 214, 190))
    # 床: 同じ紋様が刻まれた円環
    d.ellipse([340, 520, 940, 700], outline=(80, 86, 110), width=4)
    d.ellipse([420, 545, 860, 675], outline=(60, 66, 90), width=2)
    d.ellipse([620, 595, 660, 625], fill=(140, 132, 104))
    save(img, "bg_star_room.jpg", "star room")


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
    bg_road()
    bg_village()
    bg_lake_night()
    bg_cliff_door()
    bg_cathedral()
    bg_star_room()
    print("done.")
