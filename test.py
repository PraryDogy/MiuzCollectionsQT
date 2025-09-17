import cv2
import numpy as np


def highlight_blue_areas(image: np.ndarray, min_area: int = 500) -> tuple[np.ndarray, float]:
    """
    Находит синие области, закрашивает их красным и возвращает процент закрашенной площади.
    
    Returns:
        output: изображение с закрашенными областями
        percent: доля закрашенной площади в процентах
    """
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    lower_blue = np.array([85, 40, 40])
    upper_blue = np.array([160, 255, 255])
    mask = cv2.inRange(hsv, lower_blue, upper_blue)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    output = image.copy()
    # создаём пустую маску для подсчёта площади
    filled_mask = np.zeros_like(mask)

    for cnt in contours:
        if cv2.contourArea(cnt) >= min_area:
            cv2.drawContours(output, [cnt], -1, (0, 0, 255), cv2.FILLED)
            cv2.drawContours(filled_mask, [cnt], -1, 255, cv2.FILLED)

    percent = (cv2.countNonZero(filled_mask) / (image.shape[0] * image.shape[1])) * 100
    return output, round(percent, 2)




src = '/Users/Loshkarev/Desktop/2025-09-17 14.34.21.jpg'
img = cv2.imread(src)
blues, percent = highlight_blue_areas(img)
print(percent)
cv2.imshow("123", blues)
cv2.waitKey(0)