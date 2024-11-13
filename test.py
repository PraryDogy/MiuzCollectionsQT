import os


images = "/Users/Morkowik/Desktop/Evgeny/sample images"
hash = "/Users/Morkowik/Library/Application Support/MiuzCollectionsQT/hashdir"

images_len = 0
hash_len = 0

for root, dir, files in os.walk(images):
    for file in files:
        images_len += 1

for root, dir, files in os.walk(hash):
    for file in files:
        hash_len += 1

print("src", images_len)
print("hash", hash_len)