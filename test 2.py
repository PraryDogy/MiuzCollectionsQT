import os

filepath = "/Users/Loshkarev/Desktop/test.txt"
with open(filepath, "a") as file:
    sep = f"\n\n=====\n\n"
    text = "hello world"
    file.write(sep + text)