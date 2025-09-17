import cv2
import numpy as np


import cv2
import numpy as np

class ColorHighlighter:
    # словарь цветов для поиска: ключ — название, значение — (lower HSV, upper HSV)
    search_colors = {
        # "blue": (np.array([85, 40, 40]), np.array([160, 255, 255])),
        "blue": (np.array([100, 80, 80]), np.array([140, 255, 255])),
        # можно добавлять другие цвета, например:
        # "red": (np.array([0, 100, 100]), np.array([10, 255, 255]))
    }

    @classmethod
    def highlight_colors(cls, image: np.ndarray, min_area: int = 500) -> tuple[np.ndarray, dict]:
        """
        Закрашивает области для всех цветов из search_colors.
        Возвращает изображение и словарь с процентом площади каждого цвета.
        """
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        output = image.copy()
        percent_dict = {}

        for color_name, (lower, upper) in cls.search_colors.items():
            mask = cv2.inRange(hsv, lower, upper)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            filled_mask = np.zeros_like(mask)
            for cnt in contours:
                if cv2.contourArea(cnt) >= min_area:
                    cv2.drawContours(output, [cnt], -1, (0, 0, 255), cv2.FILLED)  # красная заливка
                    cv2.drawContours(filled_mask, [cnt], -1, 255, cv2.FILLED)

            percent = (cv2.countNonZero(filled_mask) / (image.shape[0] * image.shape[1])) * 100
            percent_dict[color_name] = round(percent, 2)

        return output, percent_dict


src = input().strip().strip("'").strip("\'")
img = cv2.imread(src)
blues, percent = ColorHighlighter.highlight_colors(img)
print(percent)
cv2.imshow("123", blues)
cv2.waitKey(0)