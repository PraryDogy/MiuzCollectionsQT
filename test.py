import os

from cfg import Static


def include_files_2(source_dir):
    data_files = []
    for root, dirs, files in os.walk(source_dir):
        if files:
            clean_files = [os.path.join(root, f) for f in files if f != '.DS_Store']
            if clean_files:
                data_files.append((root, clean_files))
    return data_files


def include_files(folder_name: str) -> list[str, list]:
    return (
        folder_name,
        [i.path for i in os.scandir(folder_name)]
    )

test = include_files(Static.scripts)
print(test)


test = include_files_2(Static.scripts)
print(test)