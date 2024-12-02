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

TIMER = "timer"
RES = "res"


def timer_(func: callable):

    def wrapper(*args, **kwargs):
        start = time()
        res = func(*args, **kwargs)
        end = time() - start
        return {TIMER: end, RES: res}

    return wrapper


class Test:

    def get_image_item(self, src: str) -> list[tuple[str, int, int, int]]:
        try:
            stats = os.stat(path=src)
            return (src, stats.st_size, stats.st_birthtime, stats.st_mtime)
        except FileNotFoundError as e:
            return None
        
    @timer_
    def walk_collection(self, collection: str) -> dict[str, str]:
        finder_images: list[tuple[str, int, int, int]] = []

        for root, _, files in os.walk(collection):
            for file in files:
                if file.endswith(IMG_EXT):
                    src = os.path.join(root, file)
                    stats = os.stat(src)
                    data = (src, stats.st_size, stats.st_birthtime, stats.st_mtime)
                    finder_images.append(data)

        finder_images = sorted(finder_images)
        return finder_images

    @timer_
    def tree2list(self, directory: str) -> dict[str, str]:
        result = []
        stack = [directory]
        
        while stack:
            current_dir = stack.pop()
            
            with os.scandir(current_dir) as entries:
                for entry in entries:
                    if entry.is_dir():
                        stack.append(entry.path)
                    elif entry.name.endswith(IMG_EXT):
                        stats = entry.stat()
                        data = (entry.path, stats.st_size, stats.st_birthtime, stats.st_mtime)
                        result.append(data)

        return result


# src = "/Users/Morkowik/Desktop/Evgeny/_miuz"
src = "/Volumes/Shares/Studio/MIUZ/Photo/Art/Ready"
test = Test()
walk = test.walk_collection(src)
scan_dir = test.tree2list(src)

times = {
    "walk": walk.get(TIMER),
    "scandir": scan_dir.get(TIMER)
}

faster = min(times, key=times.get)
slower = max(times, key=times.get)
offset = round(times.get(slower) / times.get(faster), 2)
offset = f"{faster} is faster than {slower} in {offset} times"
print(offset, sep="\n")

# print(scan_dir.get(RES)[0])
# print(walk.get(RES)[0])