import cv2
import os
from cfg import Static

def get_color_histogram(image):
    """Вычисляет нормализованную гистограмму в пространстве HSV."""
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    # Считаем по двум каналам: Hue (цвет) и Saturation (насыщенность)
    hist = cv2.calcHist([hsv], [0, 1], None, [50, 60], [0, 180, 0, 256])
    cv2.normalize(hist, hist, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
    return hist

def compare_images_features(sift, des_src, thumbnail):
    """Проверка по ключевым точкам (SIFT)."""
    gray_thumbnail = cv2.cvtColor(thumbnail, cv2.COLOR_BGR2GRAY)
    kp_thumb, des_thumb = sift.detectAndCompute(gray_thumbnail, None)

    if des_src is None or des_thumb is None or len(des_thumb) < 10:
        return 0

    index_params = dict(algorithm=1, trees=5)
    search_params = dict(checks=50)
    flann = cv2.FlannBasedMatcher(index_params, search_params)
    
    matches = flann.knnMatch(des_thumb, des_src, k=2)

    good_matches = []
    for m, n in matches:
        if m.distance < 0.7 * n.distance:
            good_matches.append(m)

    score = min(int((len(good_matches) / len(kp_thumb)) * 100), 100) 
    return score

# --- Подготовка эталона ---
src_img_path = '/Users/evlosh/Desktop/R1-01777-0006 А4.jpg'
src_img = cv2.imread(src_img_path)

h_src, w_src = src_img.shape[:2]
max_side = 500
if max(h_src, w_src) > max_side:
    scale = max_side / max(h_src, w_src)
    src_img = cv2.resize(src_img, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

# Извлекаем признаки из исходника один раз ДО цикла
src_hist = get_color_histogram(src_img)

sift = cv2.SIFT_create()
gray_src = cv2.cvtColor(src_img, cv2.COLOR_BGR2GRAY)
kp_src, des_src = sift.detectAndCompute(gray_src, None)

# --- Цикл сканирования директорий ---
for i in os.scandir(Static.external_hashdir):
    if i.is_dir():
        for x in os.scandir(i.path):
            if x.name.endswith(".jpg"):
                thumbnail = cv2.imread(x.path)
                if thumbnail is None:
                    continue
                
                # 1. Проверка по цвету
                thumb_hist = get_color_histogram(thumbnail)
                hist_similarity = cv2.compareHist(src_hist, thumb_hist, cv2.HISTCMP_CORREL)
                color_score = int(hist_similarity * 100)
                
                # 2. Проверка по точкам
                sift_score = compare_images_features(sift, des_src, thumbnail)
                
                # Условие: картинка подходит, если совпали И цвета, И геометрия
                if sift_score > 70 or color_score > 60:
                    print(f"🔥 Найдено! {x.name} | Цвет: {color_score}% | Точки: {sift_score}%")
                    cv2.imshow("1", thumbnail)
                    cv2.waitKey(0)

cv2.destroyAllWindows()
