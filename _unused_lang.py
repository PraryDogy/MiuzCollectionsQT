import os
import re


def find_unused_languages():
    EXTS = (".py", ".qss")
    EXCLUDED = {".git", ".venv", "venv", "__pycache__", "env", ".env"}

    lang_file = "./system/lang.py"
    unused_file = "./system/lang_unused.txt"

    with open(lang_file, "r", encoding="utf-8") as f:
        lang_content = f.read()

    # Берём содержимое класса Lng
    class_match = re.search(
        r"class\s+Lng\s*:(.*?)(?=^class\s|\Z)",
        lang_content,
        re.MULTILINE | re.DOTALL,
    )

    if not class_match:
        return []

    class_content = class_match.group(1)

    # Находим имена атрибутов:
    #
    # months = ...
    # months_gen = ...
    # file_size = ...
    #
    # Неважно, что находится после "="
    fields = re.findall(
        r"(?m)^\s{4}([A-Za-z_][A-Za-z0-9_]*)\s*=",
        class_content,
    )

    # Все файлы проекта
    project_files = []

    for root, dirs, files in os.walk("./"):
        dirs[:] = [
            d for d in dirs
            if d not in EXCLUDED
        ]

        for filename in files:
            if filename.endswith(EXTS):
                project_files.append(
                    os.path.join(root, filename)
                )

    # Содержимое всех файлов
    contents = []

    for filename in project_files:
        if os.path.abspath(filename) == os.path.abspath(lang_file):
            continue

        try:
            with open(filename, "r", encoding="utf-8") as f:
                contents.append(f.read())
        except (UnicodeDecodeError, OSError):
            pass

    # Ищем неиспользуемые
    unused = []

    for field in fields:
        pattern = rf"\bLng\.{re.escape(field)}\b"

        if not any(re.search(pattern, content) for content in contents):
            unused.append(field)

    if not unused:
        return []

    # --------------------------------------------------
    # Сохраняем удаляемые блоки
    # --------------------------------------------------

    removed_blocks = []

    for field in unused:

        # От начала строки с "field ="
        # до следующего атрибута класса или конца класса.
        pattern = re.compile(
            rf"(?ms)"
            rf"^(\s{{4}}{re.escape(field)}\s*=)"
            rf".*?"
            rf"(?=^\s{{4}}[A-Za-z_][A-Za-z0-9_]*\s*=|\Z)"
        )

        match = pattern.search(lang_content)

        if match:
            removed_blocks.append(
                match.group(0).rstrip()
            )

            lang_content = (
                lang_content[:match.start()]
                + lang_content[match.end():]
            )

    # --------------------------------------------------
    # Записываем удалённое
    # --------------------------------------------------

    with open(unused_file, "w", encoding="utf-8") as f:
        for block in removed_blocks:
            f.write(block)
            f.write("\n\n")

    # --------------------------------------------------
    # Сохраняем lang.py
    # --------------------------------------------------

    with open(lang_file, "w", encoding="utf-8") as f:
        f.write(lang_content)

    return unused


if __name__ == "__main__":
    for field in find_unused_languages():
        print(f"Удалён: Lng.{field}")