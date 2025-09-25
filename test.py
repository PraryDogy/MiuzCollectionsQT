lst = ["a", "b", "c", "b", "d", "dfds", "21323dd"]
find = "b"
ind = max(x for x, i in enumerate(lst) if i == find)


new = lst[:ind]

print(new)