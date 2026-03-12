import os


src_one = '/Volumes/Shares/Studio/Panacea/Photo/Art/Ready/0 No collection/1 IMG/IMG_2212.psd'
src_two = '/Volumes/Shares/Studio/Panacea/Photo/Art/Ready/0 No collection/1 IMG/IMG_2226.psd'

for i in (src_one, src_two):
    stats = os.stat(i)
    birth = stats.st_birthtime

    print(birth)