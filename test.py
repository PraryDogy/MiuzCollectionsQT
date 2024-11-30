import os
from pathlib import Path
from time import time

_IMG_EXT: tuple = (
    ".jpg", ".jpeg", ".jfif",
    ".tif", ".tiff",
    ".psd", ".psb",
    ".png",
    )

IMG_EXT: tuple = tuple(
    upper_ext
    for ext in _IMG_EXT
    for upper_ext in (ext, ext.upper())
    )


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

            for file in files:

                if file.endswith(IMG_EXT):
                    src = os.path.join(root, file)
                    item = self.get_image_item(src)
                    if item:
                        finder_images.append(item)

        return finder_images
    
    @timer_
    def pathlib_collection(self, collection: str) -> list[tuple[str, int, int, int]]:
        finder_images: list[tuple[str, int, int, int]] = []

        for path in Path(collection).rglob("*"):

            if path.suffix.lower() in IMG_EXT:

                finder_images.append((str(path), path.stat()))

        
        return finder_images



src = "/Users/Morkowik/Desktop/Evgeny/_miuz"
a = Test()

walk = a.walk_collection(src)
path_lib = a.pathlib_collection(src)