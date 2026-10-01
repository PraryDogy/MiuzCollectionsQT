import os
import re


def find_quoted_text():
    EXCLUDED = {".git", ".venv", "venv", "__pycache__", "env", ".env"}
    project_root = os.path.dirname(os.path.abspath(__file__))

    # Одинарные или двойные кавычки
    pattern = re.compile(r"""(["'])(.*?)(?<!\\)\1""", re.DOTALL)

    for root, dirs, files in os.walk(project_root):
        dirs[:] = [d for d in dirs if d not in EXCLUDED]

        for filename in files:
            if not filename.endswith(".py"):
                continue

            py_file = os.path.join(root, filename)

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()
            except (UnicodeDecodeError, OSError):
                continue

            for match in pattern.finditer(content):
                text = match.group(2)

                if text.strip():
                    print(f"{py_file}: {text}")


if __name__ == "__main__":
    find_quoted_text()