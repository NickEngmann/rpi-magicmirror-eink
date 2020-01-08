#!/usr/bin/env python3
import asyncio
import logging
import tempfile
import argparse
import sys
import numpy as np
from aiocron import crontab
from pyppeteer import launch
from PIL import Image

# TODO fix ignored KeyboardInterrupt when running in the the event loop (run_forever)
# TODO implement proper reset and shutdown of the screen when the systemd service is stopped or the raspberry pi is shut down
# TODO maybe a "last updated" time (just a clock module with a different header)

# Import the waveshare folder (containing the waveshare display drivers) without refactoring it to a module
# TODO maybe switch to a git submodule here and upgrade to the latest version:
# https://github.com/waveshare/e-Paper/blob/master/RaspberryPi%26JetsonNano/python/lib/waveshare_epd/epd7in5_V2c.py
sys.path.insert(0, './waveshare')
import epd7in5_V2


# Global config
display_width = 480		# Width of the display
display_height = 800		# Height of the display
is_portrait = True		# True of the display should be in landscape mode (make sure to adjust the width and height accordingly)
wait_to_load = 60		# Page load timeout
wait_after_load = 18		# Time to evaluate the JS afte the page load (f.e. to lazy-load the calendar data)
url = 'http://localhost:8080'	# URL to create the screenshot of

def reset_screen():
    epd = epd7in5_V2.EPD()
    epd.init()
    Limage = Image.new('1', (epd.height, epd.width), 255)  # 255: clear the frame
    epd.display(epd.getbuffer(Limage))


async def create_screenshot(file_path):
    global display_width
    global display_height
    global wait_to_load
    global wait_after_load
    global url
    logging.debug('Creating screenshot')
    browser = await launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox', '--headless', '--disable-gpu', '--disable-dev-shm-usage'], executablePath='/usr/bin/chromium-browser')
    page = await browser.newPage()
    await page.setViewport({
        "width": display_width,
        "height": display_height
    })
    await page.goto(url, timeout=wait_to_load * 1000)
    await page.waitFor(wait_after_load * 1000);
    await page.screenshot({'path': file_path})
    await browser.close()
    logging.debug('Finished creating screenshot')


def remove_aliasing_artefacts(image):
    red = (255,000,000)
    black = (000,000,000)
    white = (255,255,255)
    img = image.convert('RGB')
    data = np.array(img)
    # If the R value of the pixel is less than 50, make it black
    black_mask = np.bitwise_and(data[:,:,0] <= 230, data[:,:,1] <= 135, data[:,:,2] <= 135)
    # If the R value is higher than
    red_mask = np.bitwise_and(data[:,:,0] >= 230, data[:,:,1] <= 135, data[:,:,2] <= 135)
    # Everything else should be white
    white_mask = np.bitwise_not(np.bitwise_or(red_mask, black_mask))
    data[black_mask] = black
    data[red_mask] = red
    data[white_mask] = white
    return Image.fromarray(data, mode='RGB')


async def refresh():
    logging.info('Starting refresh.')
    logging.debug('Initializing / waking screen.')
    epd = epd7in5_V2.EPD()
    epd.init()
    with tempfile.NamedTemporaryFile(suffix='.png') as tmp_file:
        logging.debug(f'Created temporary file at {tmp_file.name}.')
        await create_screenshot(tmp_file.name)
        logging.debug('Opening screenshot.')
        image = Image.open(tmp_file)
        # Replace all colors with are neither black nor red with white
        image = remove_aliasing_artefacts(image)
        # Rotate the image by 90°
        if is_portrait:
           logging.debug('Rotating image (portrait mode).')
           image = image.rotate(90)
        logging.debug('Sending image to screen.')
        # epd.display_frame(epd.get_frame_buffer(image))
        epd.display(epd.getbuffer(image))
    logging.debug('Sending display back to sleep.')
    epd.sleep()
    logging.info('Refresh finished.')


def main():
    try:
        parser = argparse.ArgumentParser(description='Python EInk MagicMirror')
        parser.add_argument('-d', '--debug', action='store_true', dest='debug',
                            help='Enable debug logs.', default=False)
        parser.add_argument('-c', '--cron', action='store', dest='cron',
                            help='Sets a schedule using cron syntax')
        parser.add_argument('-r', '--reset', action='store_true', dest='reset',
                            help='Ignore all other settings and just reset the screen.', default=False)
        args = parser.parse_args()
        level = logging.DEBUG if args.debug else logging.INFO
        logging.basicConfig(level=level, format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')

        if not args.reset:
            if args.cron:
                logging.info(f'Scheduling the refresh using the schedule "{args.cron}".')
                crontab(args.cron, func=refresh)
                # Initially refresh the display before relying on the schedule
                asyncio.get_event_loop().run_until_complete(refresh())
                asyncio.get_event_loop().run_forever()
            else:
                logging.info('Only running the refresh once.')
                asyncio.get_event_loop().run_until_complete(refresh())
    except KeyboardInterrupt:
        logging.info('Shutting down after receiving a keyboard interrupt.')
    finally:
        logging.info('Resetting screen.')
        reset_screen()


if __name__ == '__main__':
    main()
