import os

def shorten_path(path: str, max_len=50):
    splited = path.strip(os.sep).split(os.sep)
    max_len = max_len - len(splited[0]) - len(splited[-1])
    while len(os.sep.join(splited[1:-1])) > max_len:
        splited.pop(1)
    splited.insert(1, "...")
    return os.sep + os.sep.join(splited)


src = "/Volumes/Shares/Studio/MIUZ/Photo/Art/Ready/4 Royal/2 Model IMG/R2022-SA4125R.tif"
a = shorten_path(src)
print(a)