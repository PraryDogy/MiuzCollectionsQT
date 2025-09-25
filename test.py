lst = ["a", "b", "c", "b", "d"]
find = "b"
ind = max(x for x, i in enumerate(lst) if i == find)
print(ind)