import os

import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim

from cfg import Static
from system.shared_utils import ImgUtils
from system.utils import Utils


import cv2
import numpy as np

import cv2
import numpy as np

def get_central_crop(img, size=210):
    h, w = img.shape[:2]
    actual_size = min(h, w, size)
    start_x = (w - actual_size) // 2
    start_y = (h - actual_size) // 2
    crop = img[start_y:start_y+actual_size, start_x:start_x+actual_size]
    return crop

def compare_images_smart(template_array, scene_array):

    # 1. Получаем размеры
    h_t, w_t = template_array.shape[:2]
    h_s, w_s = scene_array.shape[:2]

    # 2. Если сцена меньше шаблона, уменьшаем шаблон
    # (matchTemplate требует, чтобы шаблон был <= сцены)
    if h_s < h_t or w_s < w_t:
        # Вычисляем коэффициент масштабирования, чтобы вписаться в меньшую сторону сцены
        scale = min(w_s / w_t, h_s / h_t)
        new_w = int(w_t * scale)
        new_h = int(h_t * scale)
        # Уменьшаем шаблон
        template_array = cv2.resize(template_array, (new_w, new_h), interpolation=cv2.INTER_AREA)

    gray_template = cv2.cvtColor(template_array, cv2.COLOR_BGR2GRAY)
    gray_scene = cv2.cvtColor(scene_array, cv2.COLOR_BGR2GRAY)
    res = cv2.matchTemplate(gray_scene, gray_template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    score = int(max_val * 100)
    return {"score": score, "result_image": scene_array}


template = '/Users/Loshkarev/Desktop/template 4.jpg'
template_array = cv2.imread(template)
template_array = ImgUtils.resize(template_array, Static.max_img_size)
template_array = get_central_crop(template_array, 190)
for i in os.scandir(Static.external_hashdir):
    if not i.is_dir():
        continue
    for img in os.scandir(i.path):
        scene_array = cv2.imread(img.path)
        result = compare_images_smart(template_array, scene_array)
        if result["score"] > 60:
            cv2.imshow("111", result["result_image"])
            cv2.waitKey(0)
            print(result["score"])