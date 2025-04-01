import os


a = "/Users/Loshkarev/Desktop/Примеры камней"


for dirname in os.scandir(a):
    print(dirname.path)