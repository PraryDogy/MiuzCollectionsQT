import os
import shutil

def remove_empty_dirs():

    stop = ["env", ".git", "__pycache__"]

    dirs = [os.path.join(os.path.dirname(__file__), i)
            for i in os.listdir(os.path.dirname(__file__))
            if os.path.isdir(os.path.join(os.path.dirname(__file__), i))
            if i not in stop
            ]

    base_path = os.path.dirname(os.path.dirname(__file__))

    for xx in dirs:
        for dirpath, dirnames, filenames in os.walk(xx, topdown=False):
            # Проверка наличия только .pyc файлов или отсутствия файлов в папке
            if all(filename.endswith('.pyc') for filename in filenames) or not filenames:
                # Удаление папки
                try:
                    shutil.rmtree(dirpath)
                    print(f"Удалена папка: {dirpath.replace(base_path, '...')}")
                except Exception as e:
                    print(f"Ошибка при удалении папки {dirpath}: {e}")


remove_empty_dirs()