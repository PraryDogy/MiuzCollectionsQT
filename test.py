def test(callback: callable):
    callback(123)

def abc(*args):
    print(args)


final = test(lambda e, a=1: abc(e, a))