import requests
from haishoku.haishoku import Haishoku
import numpy as np
import colorsys
import io

def hex_to_rgb(value):
    """
    Convert a hex color string to an RGB tuple.

    Parameters:
    ------------
    value: str
        hex color string

    Returns:
    ------------
    tuple
        RGB color tuple
    """
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

def rgb_to_hex(rgb):
    return '#%02x%02x%02x' % rgb

def normalize_rgb_color(color):
    return tuple([i/255 for i in color])

def denormalize_rgb_color(color):
    return tuple([i*255 for i in color])

def rgb2hsv(color):
    color = normalize_rgb_color(color)
    color = colorsys.rgb_to_hsv(*color)
    return color

def int_rgb(color):
    return tuple([int(i) for i in color])

def hsv2rgb(color):
    color = colorsys.hsv_to_rgb(*color)
    color = denormalize_rgb_color(color)
    color = int_rgb(color)
    return color

def str2color(string, Azure_key, num=5, verbose=False, vi=True):
    if num>150:
        raise Exception("num must small than 150")
    search_url = "https://api.bing.microsoft.com/v7.0/images/search"
    headers = {"Ocp-Apim-Subscription-Key" : Azure_key}
    # headers2 = {"user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36"}
    params  = {"q": string}
    response = requests.get(search_url, headers=headers, params=params)
    response.raise_for_status()
    search_results = response.json()
    thumbnail_urls = [img["thumbnailUrl"] for img in search_results["value"]]
    color_list = []
    for i in range(num):
        # time.sleep(0.5)
        try:
            # img_data = requests.get(thumbnail_urls[i], headers=headers2)
            # do_color = np.array(Haishoku.getDominant(io.BytesIO(img_data.content)))
            do_color = np.array(Haishoku.getDominant(thumbnail_urls[i]))
            color_list.append(do_color)
            if verbose:
                print(i, thumbnail_urls[i], do_color)
        except:
            print("error: %s"%thumbnail_urls[i])
    color_list = np.vstack(color_list)
    rgb_color = np.mean(color_list, axis=0)
    rgb_color = rgb_color.astype("int")
    rgb_color = tuple(rgb_color)
    hsl_color = rgb2hsv(rgb_color)
    hsl_color = (hsl_color[0], 1, 0.7)
    modified_rgb = hsv2rgb(hsl_color)
    
    if vi:
         pass       

    return modified_rgb, color_list
