from difflib import SequenceMatcher
import os

class FindTiffBase:
    def __init__(self, src: str):
        super().__init__()
        self.src = src

    def similar(self, jpg: str, tiff: str):
        return SequenceMatcher(None, jpg, tiff).ratio()

    def get_result(self):
        root, jpg = os.path.split(self.src)
        jpg_no_ext, ext = jpg.split(".")

        files = {
            f: f.split(".")[0]
            for f in os.listdir(root)
            if f.lower().endswith((".tiff", ".tif", ".psd", ".psb"))
            }

        files_ratio = {
            tiff_ext: self.similar(jpg_no_ext, tiff_no_ext)
            for tiff_ext, tiff_no_ext in files.items()
            }
        
        files_ratio = {
            k: v
            for k, v in files_ratio.items()
            if v > 0.7
        }
        
        try:
            return max(files_ratio, key=files_ratio.get)
        except Exception:
            return ""




img = "/Users/Morkowik/Desktop/Evgeny/sample images/tiff_psd_images 2/2021-10-14 11-33-17 (B,Radius4,Smoothing2).jpg"
a = FindTiffBase(src=img)
b = a.get_result()

print(b)