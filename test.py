import os

volumes = "Volumes"
zip_file = "Studio/Photo/Art/Raw/2024/soft/MiuzCollections.zip"

filename_zip_file = os.path.basename(zip_file)
filename_app_file = os.path.splitext(filename_zip_file)[0] + ".app"

drives = os.listdir(os.path.join(os.sep, volumes))
drives = [
    os.path.join(os.sep, volumes, drive)
    for drive in drives
    ]

try:
    zip_file = [
        os.path.join(drive, zip_file)
        for drive in drives
        if os.path.exists(os.path.join(drive, zip_file))
        ][0]
    
except Exception as e:
    print(e)