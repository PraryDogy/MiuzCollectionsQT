def test(callback: callable):
    for i in range(0, 10):
        callback(i)


test(
    callback=lambda v: print(v)
)