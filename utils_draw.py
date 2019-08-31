#!/usr/bin/env python3

from PIL import Image, ImageDraw, ImageFont, ImageOps
from loguru import logger


def gen_preview(black_image, red_image):
    if black_image.size != red_image.size:
        logger.warning("Black and Red images has different size!")
    preview = Image.new('RGB', black_image.size, "white")  # 298*126
    preview_draw = ImageDraw.Draw(preview)
    preview.paste(black_image, (0, 0))
    revert_red = ImageOps.invert(red_image.convert('RGB')).convert('1')
    preview_draw.bitmap((0, 0), revert_red, fill="darkred")
    return preview


def draw_grid(image, step):
    w, h = image.size
    draw = ImageDraw.Draw(image)
    for i in range(0, w, step):
        draw.line((i, 0, i, h), fill=0)
    for i in range(0, h, step):
        draw.line((0, i, w, i), fill=0)


def draw_centered_text(image, text, pos_y, font_name, font_size):
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_name, font_size)
    w, h = draw.textsize(text, font=font)
    x = (image.size[0]-w)/2
    y = pos_y
    draw.text((x, y), text, font=font, fill=0)
    return (x, y, w, h)


def get_text_fit(image, text, maxsize, fontname, fontsize_min, fontsize_max):
    """
    finds good text size/text combination to fit text into maxsize piexels
    - first it trying to reduce font size from fontsize_max to fontsize_min
    - if text doesn't fit even with fontsize_min it is trying to reduce
      text length
    """

    good_size = None
    good_text = text

    draw = ImageDraw.Draw(image)

    for size in range(fontsize_max, fontsize_min, -1):
        font = ImageFont.truetype(fontname, size)
        text_size, _ = draw.textsize(good_text, font)
        logger.debug(f"size = {size} text_size = {text_size}")
        if text_size < maxsize:
            good_size = size
            logger.debug(f"found good_size = {good_size}")
            break

    if good_size is None:
        logger.debug("no good_size found. Truncating text")
        for i in range(max(2, len(good_text)-1), 0, -1):
            test_text = good_text[:i]+"…"
            font = ImageFont.truetype(fontname, fontsize_min)
            text_size, _ = draw.textsize(test_text, font)
            if text_size < maxsize:
                good_size = fontsize_min
                good_text = test_text
                logger.debug(f"found good_text = \"{good_text}\" with good_size = {good_size}")  # noqa
                break

    return good_text, good_size


def get_font_height(image, fontname, fontsize):
    draw = ImageDraw.Draw(image)
    _, max_height = draw.textsize(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz01234567890,-.",
        font=ImageFont.truetype(fontname, fontsize)
    )
    return max_height
