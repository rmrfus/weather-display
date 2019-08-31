import epd2in13b
from utils import calc_timing
from loguru import logger


@calc_timing
def draw_epaper_horizontal(black_image, red_image):
    logger.info("Sending images to e-Paper")
    epd = epd2in13b.EPD()
    epd.init()
    # epd.Clear()
    epd.display(
        epd.getbuffer(black_image.rotate(180)),
        epd.getbuffer(red_image.rotate(180))
    )
    epd.wait_until_idle()
    epd.sleep()
    logger.info("Done")
