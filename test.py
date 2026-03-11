test = [i for i in range(0, 100)]
step = 10
chunks = [
    test[i:i+step]
    for i in range(0, len(test), step)
]

print(chunks)