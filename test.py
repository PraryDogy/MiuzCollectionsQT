import os
from cfg import Static

a = os.path.join("images", "icon.icns")
b = "./images/icon.icns"

for i in (a, b):
    print(os.path.exists(i))