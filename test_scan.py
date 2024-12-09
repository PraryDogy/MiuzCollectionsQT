import os

import sqlalchemy

from cfg import Static
from database import THUMBS, Dbase


class ScanerTools:
    can_scan = True


class Items:

    def get_finder_items(self, src: str):
        finder_images = []
        stack = []
        stack.append(src)

        while stack:
            current_dir = stack.pop()

            with os.scandir(current_dir) as entries:

                for entry in entries:

                    # нельзя удалять
                    # это прервет FinderImages, но не остальные классы
                    if not ScanerTools.can_scan:
                        return finder_images

                    if entry.is_dir():
                        stack.append(entry.path)

                    elif entry.name.endswith(Static.IMG_EXT):
                        finder_images.append(self.get_file_data(entry))

    def get_file_data(self, entry: os.DirEntry) -> tuple[str, int, int, int]:
        """Получает данные файла."""
        stats = entry.stat()
        return (
            entry.path,
            int(stats.st_size),
            int(stats.st_birthtime),
            int(stats.st_mtime),
        )

    def get_db_items(self, coll: str, brand: str):
        conn = Dbase.engine.connect()

        q = sqlalchemy.select(
            THUMBS.c.short_hash,
            THUMBS.c.short_src,
            THUMBS.c.size,
            THUMBS.c.birth,
            THUMBS.c.mod
            )
        
        q = q.where(THUMBS.c.brand == brand)
        q = q.where(THUMBS.c.coll == coll)

        # не забываем относительный путь к изображению преобразовать в полный
        # для сравнения с finder_items
        res = conn.execute(q).fetchall()
        conn.close()