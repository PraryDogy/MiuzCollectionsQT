import os
import shutil


class LangAdmin:

    @classmethod
    def start(cls):
        print("1 remove empty folders and pyc files")

        user_input = input()

        if user_input == "1":
            cls.remove_empty_dirs()

    @classmethod
    def remove_empty_dirs(cls):
        exclude = ["env", ".git", "__pycache__"]
        base_path = os.path.dirname(__file__)

        for root, dirs, files in os.walk(base_path):

            dirs[:] = [d for d in dirs if d not in exclude]

            if (
                all(filename.endswith('.pyc') for filename in files)
                or
                not files
                ):

                try:
                    shutil.rmtree(root)
                    print(f"Удалена папка: {root.replace(base_path, '...')}")
                except Exception as e:
                    print(f"Ошибка при удалении папки {root}: {e}")

LangAdmin.start()