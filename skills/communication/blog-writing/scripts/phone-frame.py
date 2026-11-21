#!/usr/bin/env python3
"""Put a phone screenshot in a simple iPhone-style frame on a transparent canvas.

Usage: phone-frame.py <screenshot.png> <out.png> [--phone-height 1100] [--canvas 1600x1240]

The canvas is wider than the phone, so a blog that stretches images to the column
width shows the phone at roughly real-phone size instead of a full-width screenshot.
Pixelate private data before framing (the frame does not hide anything).
"""
import argparse

from PIL import Image, ImageDraw, ImageFilter


def rounded_mask(size, radius):
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius=radius, fill=255)
    return mask


def frame(shot_path, out_path, phone_height, canvas_size):
    shot = Image.open(shot_path).convert("RGB")
    bezel = round(phone_height * 0.018)
    screen_h = phone_height - 2 * bezel
    screen_w = round(shot.width * screen_h / shot.height)
    shot = shot.resize((screen_w, screen_h), Image.LANCZOS)
    phone_w = screen_w + 2 * bezel
    outer_r = round(phone_w * 0.16)
    inner_r = outer_r - bezel

    phone = Image.new("RGBA", (phone_w, phone_height), (0, 0, 0, 0))
    body = Image.new("RGBA", (phone_w, phone_height), (29, 29, 31, 255))
    phone.paste(body, (0, 0), rounded_mask(body.size, outer_r))
    # thin lighter rim so the edge reads on dark backgrounds too
    ImageDraw.Draw(phone).rounded_rectangle((1, 1, phone_w - 2, phone_height - 2), radius=outer_r,
                                            outline=(88, 88, 92, 255), width=2)
    phone.paste(shot, (bezel, bezel), rounded_mask(shot.size, inner_r))

    cw, ch = canvas_size
    canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    x, y = (cw - phone_w) // 2, (ch - phone_height) // 2
    # side buttons
    d = ImageDraw.Draw(canvas)
    bw = max(4, bezel // 2)
    for top, length in ((0.20, 0.06), (0.29, 0.10), (0.41, 0.10)):
        d.rounded_rectangle((x - bw, y + phone_height * top, x + 2, y + phone_height * (top + length)),
                            radius=bw, fill=(45, 45, 48, 255))
    d.rounded_rectangle((x + phone_w - 2, y + phone_height * 0.30, x + phone_w + bw, y + phone_height * 0.45),
                        radius=bw, fill=(45, 45, 48, 255))
    # soft shadow
    shadow = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((x + 6, y + 14, x + phone_w + 6, y + phone_height + 14),
                                             radius=outer_r, fill=(0, 0, 0, 70))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    canvas = Image.alpha_composite(shadow, canvas)
    canvas.alpha_composite(phone, (x, y))
    canvas.save(out_path, optimize=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("shot")
    p.add_argument("out")
    p.add_argument("--phone-height", type=int, default=1100)
    p.add_argument("--canvas", default="1600x1240")
    a = p.parse_args()
    w, h = (int(v) for v in a.canvas.split("x"))
    frame(a.shot, a.out, a.phone_height, (w, h))
