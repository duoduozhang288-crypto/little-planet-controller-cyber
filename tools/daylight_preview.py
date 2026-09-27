#!/usr/bin/env python3
"""
【早期版本 · 已被 daylight_texture.py 取代，仅作记录保留】

这一版只做「幂律提亮 + 通道增益」，实测效果不行：原贴图是高饱和紫蓝夜景，
单纯提亮会得到一团粉色噪点。请用 tools/daylight_texture.py（HSV 域处理）。

把赛博星球的夜景 basecolor 贴图重做成「白天版」，并输出对比预览图。

思路（不引入任何 AI 重绘，纯色彩变换，保证与原配色关系一致）：
  1. 幂律提亮：把整体均值拉到目标的白天亮度，暗部抬得多、纯白高光不动；
  2. 日光白平衡：压掉夜景偏蓝紫的冷调，往中性偏暖的日光色温拉；
  3. 饱和度/对比微调：霓虹自发光区降饱和，避免白天里「发光感」突兀。

用法：python3 tools/daylight_preview.py <basecolor> <输出预览图>
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageStat

src = Path(sys.argv[1])
out_png = Path(sys.argv[2])

base = Image.open(src).convert("RGB")
W, H = base.size
print(f"贴图尺寸 {W}x{H}")

stat = ImageStat.Stat(base)
cur_mean = sum(stat.mean) / 3
print(f"原始平均亮度 {cur_mean:.1f} / 255   通道均值 R{stat.mean[0]:.1f} G{stat.mean[1]:.1f} B{stat.mean[2]:.1f}")


def luma_mean(img):
    s = ImageStat.Stat(img)
    return (0.2126 * s.mean[0] + 0.7152 * s.mean[1] + 0.0722 * s.mean[2])


def solve_gamma(img, target_luma, lo=0.4, hi=3.0):
    """二分求 gamma：使 img^(1/gamma) 后的感知亮度接近 target_luma。"""
    lut_cache = {}

    def apply(g):
        if g not in lut_cache:
            lut = [min(255, int(round(255 * ((i / 255) ** (1.0 / g))))) for i in range(256)]
            lut_cache[g] = lut * 3
        return img.point(lut_cache[g])

    for _ in range(24):
        mid = (lo + hi) / 2
        if luma_mean(apply(mid)) < target_luma:
            lo = mid
        else:
            hi = mid
    g = (lo + hi) / 2
    return g, apply(g)


def white_balance(img, r=1.0, g=1.0, b=1.0):
    lut = []
    for ch, k in enumerate((r, g, b)):
        lut += [min(255, int(round(i * k))) for i in range(256)]
    return img.point(lut)


def daylight(img, target_luma, wb, sat, contrast):
    g, lifted = solve_gamma(img, target_luma)
    balanced = white_balance(lifted, *wb)
    balanced = ImageEnhance.Color(balanced).enhance(sat)
    balanced = ImageEnhance.Contrast(balanced).enhance(contrast)
    return balanced, g


# 三个候选：亮度递增、色温由冷转暖
presets = [
    ("晨雾清晨", 108, (1.06, 1.03, 0.94), 0.86, 1.04),
    ("正午晴日", 132, (1.04, 1.02, 0.97), 0.95, 1.10),
    ("午后暖阳", 150, (1.08, 1.01, 0.90), 1.02, 1.12),
]

results = []
for name, target, wb, sat, con in presets:
    img, g = daylight(base, target, wb, sat, con)
    lm = luma_mean(img)
    s = ImageStat.Stat(img)
    print(f"  {name}: gamma={g:.2f} 结果亮度={lm:.1f}  通道 R{s.mean[0]:.0f} G{s.mean[1]:.0f} B{s.mean[2]:.0f}")
    results.append((name, img))

# ---- 合成预览图 ----
CELL = 520
PAD = 24
LABEL = 46
cols, rows = 2, 2
pw = CELL * cols + PAD * (cols + 1)
ph = (CELL + LABEL) * rows + PAD * (rows + 1)
canvas = Image.new("RGB", (pw, ph), (18, 20, 26))
d = ImageDraw.Draw(canvas)

font_path = "/System/Library/Fonts/PingFang.ttc"
try:
    f_label = ImageFont.truetype(font_path, 22)
    f_sub = ImageFont.truetype(font_path, 15)
except Exception:
    f_label = f_sub = ImageFont.load_default()

panels = [("原版 · 赛博夜景", base)] + results
for i, (title, img) in enumerate(panels):
    cx = PAD + (i % cols) * (CELL + PAD)
    cy = PAD + (i // cols) * (CELL + LABEL + PAD)
    thumb = img.copy()
    thumb.thumbnail((CELL, CELL), Image.LANCZOS)
    canvas.paste(thumb, (cx + (CELL - thumb.width) // 2, cy + (CELL - thumb.height) // 2))
    ly = cy + CELL + 6
    d.text((cx, ly), title, font=f_label, fill=(238, 240, 248))
    lm = luma_mean(img)
    d.text((cx + 300, ly + 6), f"亮度 {lm:.0f}", font=f_sub, fill=(140, 148, 168))

canvas.save(out_png)
print(f"\n预览图已写出: {out_png}  ({pw}x{ph})")
