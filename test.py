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
        return end, res

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
    # def find_files_with_extensions(self, directory):
    #     result = []
    #     stack = [directory]
    #     while stack:
    #         current_dir = stack.pop()
    #         with os.scandir(current_dir) as entries:
    #             for entry in entries:
    #                 if entry.is_dir():
    #                     stack.append(entry.path)
    #                 elif entry.is_file() and any(entry.name.endswith(ext) for ext in IMG_EXT):
    #                     result.append(entry.path)
    #     return result

    @timer_
    def tree2list(self, directory: str) -> list:
        tree = []
        for i in os.scandir(directory):
            if i.is_dir():
                tree.append(i.path)
                tree.extend(self.tree2list(i.path))
            else:
                tree.append(i.path)
        return tree


src = "/Users/Morkowik/Desktop/Evgeny/_miuz"
test = Test()
walk = test.walk_collection(src)
scan_dir = test.tree2list(src)

times = {
    "walk": walk[0],
    "scandir": scan_dir[0]
}

faster = min(times, key=times.get)
slower = max(times, key=times.get)
offset = round(times.get(slower) / times.get(faster), 2)
offset = f"{faster} is faster than {slower} in {offset} times"
print(offset, sep="\n")