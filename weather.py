#!/usr/bin/env python3

from PIL import Image, ImageDraw, ImageFont
from epd2in13b import EPD_HEIGHT, EPD_WIDTH

from imgcat import imgcat
from geopy.geocoders import GeoNames
from loguru import logger
import requests
import click

from utils import cached, load_cache, save_cache, calc_timing
from utils_draw import get_text_fit, draw_centered_text, gen_preview, get_font_height
from utils_epaper import draw_epaper_horizontal
from config import CONFIG


DARKSKY_ICON_MAP = {
    "clear-day": "\uf00d",
    "clear-night": "\uf02e",
    "rain": "\uf019",
    "snow": "\uf01b",
    "sleet": "\uf0b5",
    "wind": "\uf050",
    "fog": "\uf014",
    "cloudy": "\uf013",
    "partly-cloudy-day": "\uf002",
    "partly-cloudy-night": "\uf031",
    "hail": "\uf015",
    "thunderstorm": "\uf01e",
    "tornado": "\uf056",
}


@cached
def get_location(address):
    logger.info(f"Determining location of {address}")
    geolocator = GeoNames(username=CONFIG["geonames_username"])
    location = geolocator.geocode(address)
    if location is None:
        logger.error(f"Unable to find address \"{address}\"")
    return location


def get_weather(location, si_units=False):

    req_units = "us"
    if si_units:
        req_units = "si"

    api_key = CONFIG["ds_api_key"]

    url = (
        "https://api.darksky.net/forecast/"
        f"{api_key}/"
        f"{location.latitude},{location.longitude}"
        f"?units={req_units}"
    )

    logger.info(f"Requesting {url}...")
    response = requests.get(url)
    if not response.ok:
        logger.warning(f"Got {response.status_code} from Dark Sky")
        return None
    return response.json()


def draw_icon_temp(
    image, weather_data, location, size,
    daily=False, draw_it=True, si_units=False
):

    draw = ImageDraw.Draw(image)
    x, y = location

    icon_text = DARKSKY_ICON_MAP[weather_data["icon"]]
    icon_font = ImageFont.truetype(CONFIG["font_weather"], size)
    (icon_w, icon_h) = draw.textsize(icon_text, font=icon_font)
    _, max_icon_h = draw.textsize(
        ''.join(DARKSKY_ICON_MAP.values()), font=icon_font
    )

    temp_sign = "ºF"
    if si_units:
        temp_sign = "ºC"

    if daily:
        temp_text = "{}/{}".format(
            int(weather_data["temperatureHigh"]),
            int(weather_data["temperatureLow"])
        )
    else:
        temp_text = "{}{}".format(int(weather_data["temperature"]), temp_sign)

    temp_font = ImageFont.truetype(CONFIG["font_temperature"], int(size*0.8))
    (temp_w, temp_h) = draw.textsize(temp_text, font=temp_font)

    gap = int(size*0.15)

    if draw_it:
        draw.text((x, y), icon_text, font=icon_font, fill=0)
        draw.text(
            (x+icon_w+gap, y+(max_icon_h-temp_h)*0.4),
            temp_text, font=temp_font, fill=0
        )

    return (icon_w+temp_w+gap, max_icon_h)


def get_nice_address(location):
    nice_address = "{toponymName}".format(**location.raw)
    if location.raw['fcl'] == 'P':
        if location.raw['countryCode'] == 'US':
            nice_address = "{toponymName}, {adminCode1}".format(**location.raw)
        else:
            nice_address = "{toponymName}, {countryName}".format(**location.raw)  # noqa
    logger.debug(f"nice_address = {nice_address}")
    return nice_address


@click.command()
@click.option("--draw/--no-draw", 'flag_draw', is_flag=True, default=False, help="Send image to e-Paper (default: no)")
@click.option("--preview/--no-preview", 'flag_preview', is_flag=True, default=True, help="Show inline preview of generated image on iTerm (default:yes)")
@click.option("--as-is/--no-as-is", 'flag_asis', is_flag=True, default=False, help="Display address as-is or try to find nice name for it (default: expand)")
@click.option("-C/-F", 'flag_si', is_flag=True, default=False, help="Units to display weather (default: F)")
@click.argument("address", nargs=-1)
def _main(flag_draw, flag_preview, flag_asis, flag_si, address):
    """
    ADDRESS - freeform address to get forecast for
    """

    address = ' '.join(address)  # ewww...
    load_cache(get_location)
    location = get_location(address)
    if not location:
        return 1
    save_cache(get_location)

    if flag_asis:
        nice_address = address
    else:
        nice_address = get_nice_address(location)

    weather = get_weather(location, flag_si)
    if weather is None or "currently" not in weather:
        return 1

    image_black = Image.new('1', (EPD_HEIGHT, EPD_WIDTH), 255)  # 298*126
    image_red = Image.new('1', image_black.size, 255)

    # estimate size of and draw forecast address
    address_text, address_size = get_text_fit(
        image_black, nice_address, image_black.size[0]-4,
        CONFIG["font_address"], CONFIG["font_address_size_min"], CONFIG["font_address_size"]
    )
    draw_centered_text(image_red, address_text, 0, CONFIG["font_address"], address_size)
    max_address_height = get_font_height(image_black, CONFIG["font_address"], CONFIG["font_address_size"])

    # estimate sizes of today/tomorrow forecasts
    (d0w, d0h) = draw_icon_temp(
        image_black, weather["daily"]["data"][0],
        (0, 0), CONFIG["font_forecast_size"],
        daily=True, draw_it=False, si_units=flag_si
    )
    (d1w, d1h) = draw_icon_temp(
        image_black, weather["daily"]["data"][1],
        (0, 0), CONFIG["font_forecast_size"],
        daily=True, draw_it=False, si_units=flag_si
    )

    # position forecasts nicely
    d_gap = (image_black.size[0]-d0w-d1w)/3
    d0x = d_gap
    d0y = image_black.size[1]-d0h-2
    d1x = d_gap+d0w+d_gap
    d1y = d0y

    # actually draw forecasts
    draw_icon_temp(
        image_black, weather["daily"]["data"][0],
        (d0x, d0y), CONFIG["font_forecast_size"],
        daily=True, si_units=flag_si
    )
    draw_icon_temp(
        image_black, weather["daily"]["data"][1],
        (d1x, d1y), CONFIG["font_forecast_size"],
        daily=True, si_units=flag_si
    )

    (cw, ch) = draw_icon_temp(
        image_black, weather["currently"],
        (0, 0), CONFIG["font_main_size"],
        daily=False, draw_it=False, si_units=flag_si
    )
    draw_icon_temp(
        image_black, weather["currently"],
        ((image_black.size[0]-cw)/2, int(max_address_height*0.9)), CONFIG["font_main_size"],
        daily=False, si_units=flag_si
    )

    if flag_preview:
        imgcat(gen_preview(image_black, image_red))
    if flag_draw:
        draw_epaper_horizontal(image_black, image_red)

    return 0


if __name__ == "__main__":
    _main()
