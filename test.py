import os
from cfg import Static

a = os.path.join("images", "icon.icns")
b = "./images/icon.icns"



app_support = os.path.expanduser("~/Library/Application Support")

APP_SUPPORT_JSON_DATA: str = f"{app_support}/cfg.json"

print(APP_SUPPORT_JSON_DATA)