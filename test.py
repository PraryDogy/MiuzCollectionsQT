import os
from pathlib import Path
from time import time

from cfg import Static
from utils.scaner import ScanerUtils

def timer_(func: callable):

    def wrapper(*args, **kwargs):
        start = time()
        res = func(*args, **kwargs)
        end = time() - start
        print(end)
        return res

    return wrapper


class Test:

    def get_image_item(self, src: str) -> list[tuple[str, int, int, int]]:
        try:
            stats = os.stat(path=src)
            return (src, stats.st_size, stats.st_birthtime, stats.st_mtime)
        except FileNotFoundError as e:
            return None
        
    @timer_
    def walk_collection(self, collection: str) -> list[tuple[str, int, int, int]]:
        finder_images: list[tuple[str, int, int, int]] = []

        for root, _, files in os.walk(collection):

            if not ScanerUtils.can_scan:
                return finder_images

            for file in files:

                if not ScanerUtils.can_scan:
                    return finder_images

                if file.endswith(Static.IMG_EXT):
                    src = os.path.join(root, file)
                    item = self.get_image_item(src)
                    if item:
                        finder_images.append(item)

        return finder_images
    
    @timer_
    def pathlib_collection(self, collection: str) -> list[tuple[str, int, int, int]]:
        finder_images: list[tuple[str, int, int, int]] = []

        for path in Path(collection).rglob("*"):

            if path.suffix.lower() in Static.IMG_EXT:

                finder_images.append((str(path), path.stat()))

        
        return finder_images



src = "/Users/Morkowik/Desktop/Evgeny/_miuz"
a = Test()

walk = a.walk_collection(src)
path_lib = a.pathlib_collection(src)

# res = min(walk, path_lib)

# if res == walk:
#     print("walk faster")
# else:
#     print("path_lib faster")
