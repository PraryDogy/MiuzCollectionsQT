def test(number_list: list[str]):
    counter = 0
    for i in range(1, len(number_list)):
        prev = number_list[i - 1]
        current = number_list[i]
        if current > prev:
            counter += 1
    return counter


number_list = input().split()
counter = test(number_list)
print(counter)