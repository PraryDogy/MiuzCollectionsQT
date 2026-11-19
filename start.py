# start.py
# Верхний уровень только лёгкий. Дочерние процессы (spawn) выполняют этот файл
# заново, поэтому здесь нет импортов окон и системных модулей.
import sys
from multiprocessing import freeze_support


def main() -> int:
    # тяжёлые импорты только в главном процессе
    from app_main import run
    return run(sys.argv)


if __name__ == "__main__":
    freeze_support()
    sys.exit(main())