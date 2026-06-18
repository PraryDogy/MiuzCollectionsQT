import cv2
import os
from cfg import Static

class ImageSearcher:
    def __init__(self, src_img, hash_dir=None, max_side=500):
        """
        Инициализация класса поиска.
        :param src_img: Исходное изображение (numpy array)
        :param hash_dir: Путь к базовой директории с подпапками (по умолчанию из Static)
        :param max_side: Максимальный размер стороны для масштабирования исходника
        """
        # self.hash_dir = hash_dir if hash_dir else Static.external_hashdir
        self.hash_dir = "/Users/Loshkarev/Desktop/hashdir"
        self.max_side = max_side
        self.sift = cv2.SIFT_create()
        
        # Предварительная подготовка эталона при создании объекта
        self.processed_src = self._prepare_source(src_img)
        self.src_hist = self._get_color_histogram(self.processed_src)
        
        gray_src = cv2.cvtColor(self.processed_src, cv2.COLOR_BGR2GRAY)
        _, self.des_src = self.sift.detectAndCompute(gray_src, None)

    def _get_color_histogram(self, image):
        """Вычисляет нормализованную гистограмму в пространстве HSV."""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1], None, [50, 60], [0, 180, 0, 256])
        cv2.normalize(hist, hist, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
        return hist

    def _compare_sift(self, thumbnail):
        """Проверка миниатюры по ключевым точкам (SIFT)."""
        gray_thumbnail = cv2.cvtColor(thumbnail, cv2.COLOR_BGR2GRAY)
        kp_thumb, des_thumb = self.sift.detectAndCompute(gray_thumbnail, None)

        if self.des_src is None or des_thumb is None or len(des_thumb) < 10:
            return 0

        index_params = dict(algorithm=1, trees=5)
        search_params = dict(checks=50)
        flann = cv2.FlannBasedMatcher(index_params, search_params)
        
        matches = flann.knnMatch(des_thumb, self.des_src, k=2)

        good_matches = []
        for m, n in matches:
            if m.distance < 0.7 * n.distance:
                good_matches.append(m)

        if not kp_thumb:
            return 0
            
        score = min(int((len(good_matches) / len(kp_thumb)) * 100), 100) 
        return score

    def _prepare_source(self, src_img):
        """Масштабирует исходное изображение, если оно больше лимита."""
        h_src, w_src = src_img.shape[:2]
        if max(h_src, w_src) > self.max_side:
            scale = self.max_side / max(h_src, w_src)
            return cv2.resize(src_img, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        return src_img.copy()

    def start(self, min_sift=70, min_color=60):
        """
        Запускает процесс сканирования директории и сравнения файлов.
        :param min_sift: Порог совпадения по точкам SIFT
        :param min_color: Порог совпадения по цвету
        """
        # Сканирование директорий
        for i in os.scandir(self.hash_dir):
            if i.is_dir():
                for x in os.scandir(i.path):
                    if x.name.endswith(".jpg"):
                        thumbnail = cv2.imread(x.path)
                        if thumbnail is None:
                            continue
                        
                        # 1. Проверка по цвету
                        thumb_hist = self._get_color_histogram(thumbnail)
                        hist_similarity = cv2.compareHist(self.src_hist, thumb_hist, cv2.HISTCMP_CORREL)
                        color_score = int(hist_similarity * 100)
                        
                        # 2. Проверка по точкам
                        sift_score = self._compare_sift(thumbnail)
                        
                        # Условие соответствия OR
                        if sift_score > min_sift or color_score > min_color:
                            print(f"🔥 Найдено! {x.name} | Цвет: {color_score}% | Точки: {sift_score}%")
                            cv2.imshow("1", thumbnail)
                            cv2.waitKey(0)

        cv2.destroyAllWindows()


img_array = cv2.imread("/Users/Loshkarev/Desktop/R01-WED-00112-MIX-или-R01-WED-00084-MIX-2.jpg")
image_sercher = ImageSearcher(img_array)
image_sercher.start()