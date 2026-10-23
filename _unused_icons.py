import os


import os


def find_unused_icons():
    EXTS = (".py", ".qss")
    EXCLUDED = {".git", ".venv", "venv", "__pycache__", "env", ".env"}
    project_root = os.path.dirname(os.path.abspath(__file__))
    icons_dir = os.path.join(project_root, "icons")

    # Полные пути ко всем файлам из icons/ и вложенных папок
    icon_paths = []

    for root, _, files in os.walk(icons_dir):
        for filename in files:
            icon_paths.append(os.path.join(root, filename))

    # Все .py и .qss файлы проекта
    code_files = []

    for root, dirs, files in os.walk(project_root):
        # Не ищем внутри виртуальных окружений и .git
        dirs[:] = [d for d in dirs if d not in EXCLUDED]

        for filename in files:
            if filename.endswith(EXTS):
                code_files.append(os.path.join(root, filename))

    # Читаем содержимое всех файлов с кодом
    contents = []

    for code_file in code_files:
        try:
            with open(code_file, "r", encoding="utf-8") as f:
                contents.append(f.read())
        except (UnicodeDecodeError, OSError):
            pass

    # Ищем неиспользуемые иконки по имени файла
    unused = []

    for icon_path in icon_paths:
        icon_name = os.path.basename(icon_path)
        if not any(icon_name in content for content in contents):
            unused.append(icon_path)

    return sorted(unused)


def delete_files(paths):
    deleted = 0

    for path in paths:
        try:
            os.remove(path)
            deleted += 1
        except OSError as e:
            print(f"Не удалось удалить {path}: {e}")

    return deleted


if __name__ == "__main__":
    unused_icons = find_unused_icons()

    if not unused_icons:
        print("Неиспользуемых иконок нет.")
    else:
        print(f"Неиспользуемые иконки ({len(unused_icons)}):")
        for icon in unused_icons:
            print(" ", os.path.relpath(icon))

        answer = input("\nУдалить эти файлы? (Y/n): ").strip().lower()

        if answer == "y":
            count = delete_files(unused_icons)
            print(f"Удалено файлов: {count}")
        else:
            print("Удаление отменено.")


if __name__ == "__main__":
    unused_icons = find_unused_icons()

    for icon in unused_icons:
        print(icon)