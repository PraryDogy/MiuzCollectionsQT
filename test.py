def test(callback: callable):
    for i in range(0, 10):
        callback("ewrwerw", i)


test(
    callback=lambda *args: print(999, *args)
)