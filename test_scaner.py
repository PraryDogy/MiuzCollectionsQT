import traceback
import os

coll_folder = "/Volumes/Shares/Collections"

stop_colls = [
    "_Archive_Commerce_Брендинг",
    "Chosed",
    "LEVIEV"
    ]

tiff_images = set()

class Manager:
    jpg_exsts = (".jpg", ".JPG", ".jpeg", ".JPEG", ".png", ".PNG")
    tiff_exsts = (".tiff", ".TIFF", ".psd", ".PSD", ".psb", ".PSB", ".tif", ".TIF")
    curr_percent = 0
    progressbar_len = 50
    flag = True

    @staticmethod
    def sleep():
        return
        sleep(0.5)

class FinderImages(dict):
    def __init__(self):
        super().__init__()

        try:
            self.run()

        except (OSError, FileNotFoundError):
            print(traceback.format_exc())
            Manager.flag = False

    def get_collections(self):
        collections = [
            os.path.join(coll_folder, i)
            for i in os.listdir(coll_folder)
            if os.path.isdir(os.path.join(coll_folder, i))
            and i not in stop_colls
            ]

        if not collections:
            collections = [coll_folder]

        return collections

    def run(self):
        collections = self.get_collections()

        try:
            step_value = Manager.progressbar_len / len(collections)
        except ZeroDivisionError as e:
            print(f"scaner > FinderImages > run, {e}")
            print("coll_folder don't have subfolders")
            step_value = 1

        float_value = 0

        # for collection_walk in collections:

        #     if not Manager.flag:
        #         return

        #     float_value += step_value

        #     if float_value >= 1:
        #         Manager.curr_percent += int(float_value)
        #         float_value = 0

        #     Manager.sleep()

        for root, dirs, files in os.walk(top=coll_folder):

            if not Manager.flag:
                return

            for file in files:

                if not Manager.flag:
                    return

                if file.endswith(Manager.jpg_exsts):
                    
                    src = os.path.join(root, file)
                    file_stats = os.stat(path=src)

                    self[src] = (
                        int(file_stats.st_size),
                        int(file_stats.st_birthtime),
                        int(file_stats.st_mtime)
                        )

                elif file.endswith(Manager.tiff_exsts):
                    tiff_images.add(os.path.join(root, file))


FinderImages()