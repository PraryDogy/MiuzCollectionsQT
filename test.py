import os

a = os.path.dirname(__file__)
print(a)

b = "/Users/Loshkarev/Documents/Разное/Progs/MiuzCollections.app/Contents/Resources"
b = b.strip().split(os.sep)[:-2]
b = os.path.join(os.sep, *b)
print(b)