import os

name = "2021-09-08 15-32-03 (B,Radius4,Smoothing2)abcdefghilkmnoprstu.jpg"
only_name, ext = os.path.splitext(name)

max_row = 28
max_chars = 45
diff = len(name) - max_row *2

if diff > 0:
    name = name[:max_chars] + "..." + only_name[-3:] + ext

if len(name) > max_row:
    name = '\n'.join(
            [name[i:i + max_row]
                for i in range(0, len(name), max_row)]
                )