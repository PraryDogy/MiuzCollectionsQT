percent = 0

def progressbar(value: int):
    global percent

    if isinstance(value, int):
        percent += value
        print(percent)
    else:
        raise TypeError

collections = [i for i in range(0, 353)]
maximum = 50
step = maximum / len(collections)


step = 0.49999

print(round(step))