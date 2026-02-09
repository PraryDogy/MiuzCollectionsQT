import os

curr_path = "Volumes/Test/Collections/"
dir_path = "hello/world/"


fin = os.path.join(
    os.sep,
    curr_path.strip(os.sep),
    dir_path.strip(os.sep)
)

print(fin)