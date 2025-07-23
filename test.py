def test(a: int, b: int, c: int):
    a = a + 1
    b = b + 1
    c = c + 1
    return a, b, c


a = 1
b = 2
c = 3
args = (a, b, c)
a, b, c = test(*args)

print(args)