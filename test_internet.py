import requests
import time

def check_internet_connection(interval=5):
    while True:
        try:
            response = requests.get("http://www.google.com", timeout=5)
            if response.status_code == 200:
                pass
        except (requests.RequestException, Exception) as e:
            print("Отсутствует интернет-соединение.")
            print(e)

        time.sleep(interval)

# Пример использования с интервалом проверки каждые 5 секунд
check_internet_connection()
