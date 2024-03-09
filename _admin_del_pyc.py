import os
import shutil

def remove_empty_dirs():

    stop = ["env", ".git", "__pycache__"]

    dirs = [os.path.join(os.path.dirname(__file__), i)
            for i in os.listdir(os.path.dirname(__file__))
            if os.path.isdir(os.path.join(os.path.dirname(__file__), i))
            if i not in stop
            ]

    for xx in dirs:
        for dirpath, dirnames, filenames in os.walk(xx, topdown=False):
            # Проверка наличия только .pyc файлов или отсутствия файлов в папке
            if all(filename.endswith('.pyc') for filename in filenames) or not filenames:
                # Удаление папки
                try:
                    shutil.rmtree(dirpath)
                    print(f"Удалена пустая или содержащая только .pyc файлы папка: {dirpath}")
                except Exception as e:
                    print(f"Ошибка при удалении папки {dirpath}: {e}")


remove_empty_dirs()