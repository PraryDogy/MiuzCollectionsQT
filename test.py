test = [i for i in range(0, 50)]

offset = -1
current_index = 0
new_index = current_index + offset

if new_index > len(test):
    new_index = 0

elif new_index < 0:
    new_index = len(test)


print(new_index)