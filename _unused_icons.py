import os


def find_unused_icons():
    EXTS = (".py", ".qss")
    EXCLUDED = {".git", ".venv", "venv", "__pycache__", "env", ".env"}
    project_root = os.path.dirname(os.path.abspath(__file__))
    icons_dir = os.path.join(project_root, "icons")

    # Все файлы из icons/ и вложенных папок
    icon_files = []

    for root, _, files in os.walk(icons_dir):
        for filename in files:
            icon_files.append(filename)

    # Все .py файлы проекта
    py_files = []

    for root, dirs, files in os.walk(project_root):
        # Не ищем внутри виртуальных окружений и .git
        dirs[:] = [
            d for d in dirs
            if d not in EXCLUDED
        ]

        for filename in files:
            if filename.endswith(EXTS):
                py_files.append(os.path.join(root, filename))

    # Читаем содержимое всех Python-файлов
    py_contents = []

    for py_file in py_files:
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                py_contents.append(f.read())
        except (UnicodeDecodeError, OSError):
            pass

    # Ищем неиспользуемые иконки
    unused = []

    for icon_name in icon_files:
        if not any(icon_name in content for content in py_contents):
            unused.append(icon_name)

    return sorted(unused)


if __name__ == "__main__":
    unused_icons = find_unused_icons()

    for icon in unused_icons:
        print(icon)