import os
import shutil
import subprocess
import zipapp




from cfg import JsonData
JsonData.init()

def get_shortpath(src: str) -> str:
    return src.replace(JsonData.coll_folder, "")

src = "/Volumes/Shares/Studio/MIUZ/Photo/Art/Ready/4 Royal/1 IMG/2022-03-16 21-15-48.psd"
res = get_shortpath(src)

print(src)
print(res)