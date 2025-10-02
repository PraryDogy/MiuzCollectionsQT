import os
from pathlib import Path

src = '/Users/Loshkarev/Desktop/Геология/IMAGE 2025-09-17 15:07:15 — копия.jpg'
path = Path(src)
print(path.exists())
# root, file = os.path.split(src)

# for i in os.scandir(root):
#     if i.name == file:
#         print(1)