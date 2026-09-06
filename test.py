non_printable = "Василий"
lst = ["Инна", non_printable, "Енот", "Автомобиль"]

# первый
for i in lst:
    if i == non_printable:
        continue
    else:
        ...
        # print


# второй
ind = lst.index(non_printable)
new_lst = lst.copy()
new_lst.pop(ind)

for i in new_lst:
    print(i)