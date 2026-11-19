import os


class StopList:
    """
    Стоп-лист по относительным путям. Папка из стоп-листа и всё её поддерево
    считаются стоп-папками: изображения в них не сканируются, структура сохраняется.
    """

    # mod для стоп-папок в Dirs. Реальный mtime никогда не равен 0.
    MOD = 0

    def __init__(self, stop_list: list[str]):
        self.roots = {
            os.sep + s.strip(os.sep)
            for s in stop_list
            if s.strip(os.sep)
        }

    def contains(self, rel_path: str) -> bool:
        rel = os.sep + rel_path.strip(os.sep)
        for root in self.roots:
            if rel == root or rel.startswith(root + os.sep):
                return True
        return False
