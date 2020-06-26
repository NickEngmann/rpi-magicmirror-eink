  
##
 #  @filename   :   main.cpp
 #  @brief      :   7.5inch e-paper display demo
 #  @author     :   Yehui from Waveshare
 #
 #  Copyright (C) Waveshare     July 28 2017
 #
 # Permission is hereby granted, free of charge, to any person obtaining a copy
 # of this software and associated documnetation files (the "Software"), to deal
 # in the Software without restriction, including without limitation the rights
 # to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 # copies of the Software, and to permit persons to  whom the Software is
 # furished to do so, subject to the following conditions:
 #
 # The above copyright notice and this permission notice shall be included in
 # all copies or substantial portions of the Software.
 #
 # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 # IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 # FITNESS OR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 # AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 # LIABILITY WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 # OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 # THE SOFTWARE.
 ##

import epd7in5bc
from PIL import Image
import logging
import PIL.ImageOps
import numpy as np

# Global config
is_portrait = False             # True of the display should be in landscape mode (make sure to adjust the width and height accordingly)
is_topdown = True

def remove_aliasing_artefacts(image):
    red = (255,000,000)
    black = (000,000,000)
    white = (255,255,255)
    img = image.convert('RGB')
    data_one = np.array(img)
    data_two = np.array(img)
    # If the R value of the pixel is less than 50, make it black
    black_mask = np.bitwise_and(data_one[:,:,0] <= 230, data_one[:,:,1] <= 135, data_one[:,:,2] <= 135)
    # If the R value is higher than
    red_mask = np.bitwise_and(data_one[:,:,0] >= 230, data_one[:,:,1] <= 135, data_one[:,:,2] <= 135)
    # Everything else should be white
    white_mask = np.bitwise_not(np.bitwise_or(red_mask, black_mask))
    data_one[black_mask] = black
    data_one[red_mask] = red
    data_one[white_mask] = white

    data_two[black_mask] = white
    data_two[red_mask] = red
    data_two[white_mask] = white
    return Image.fromarray(data_one, mode='RGB'), Image.fromarray(data_two, mode='RGB')


def main():
    logging.info('Starting refresh.')
    logging.debug('Initializing / waking screen.')
    epd = epd7in5bc.EPD()
    epd.init()

    og_image = Image.open('screenshot.png')
    # Replace all colors with are neither black nor red with white
    base_image,red_image = remove_aliasing_artefacts(og_image)
    base_image_invert = PIL.ImageOps.invert(base_image)
    red_image_invert = PIL.ImageOps.invert(red_image)
    # Rotate the image by 90
    if is_portrait:
        logging.debug('Rotating image (portrait mode).')
        invert_image = base_image.rotate(90)
    if is_topdown:
        logging.debug('Rotating image (topdown mode).')
        red_image_rotate = red_image_invert.rotate(180)
        base_image_rotate = base_image_invert.rotate(180)
    logging.debug('Sending image to screen.')
    print(base_image)
    print(red_image)
    epd.display(epd.getbuffer(base_image_invert), epd.getbuffer(red_image))
    # logging.debug('Sending display back to sleep.')
    # epd.sleep()
    logging.info('Refresh finished.')

if __name__ == '__main__':
    main()
