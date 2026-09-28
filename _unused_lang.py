import os
import re


def find_unused_languages():
    EXTS = (".py", ".qss")
    EXCLUDED = {".git", ".venv", "venv", "__pycache__", "env", ".env"}
    lang_file = "./system/lang.py"

    with open(lang_file, "r", encoding="utf-8") as f:
        lang_content = f.read()

    lng_fields = re.findall(
        r"^\s{4}([A-Za-z_][A-Za-z0-9_]*)\s*=",
        lang_content,
        re.MULTILINE,
    )

    # Все .py файлы проекта
    py_files = []

    for root, dirs, files in os.walk("./"):
        dirs[:] = [
            d for d in dirs
            if d not in EXCLUDED
        ]

        for filename in files:
            if filename.endswith(EXTS):
                py_files.append(os.path.join(root, filename))

    # Ищем использования Lng.xxx
    unused = []

    for field in lng_fields:
        pattern = re.compile(rf"\bLng\.{re.escape(field)}\b")

        used = False

        for py_file in py_files:
            # Сам lang.py не считаем использованием
            if os.path.abspath(py_file) == os.path.abspath(lang_file):
                continue

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()
            except (UnicodeDecodeError, OSError):
                continue

            if pattern.search(content):
                used = True
                break

        if not used:
            unused.append(field)

    return unused


if __name__ == "__main__":
    unused = find_unused_languages()

    for field in unused:
        print(f"Lng.{field}")