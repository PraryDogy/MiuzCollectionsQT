from collections import defaultdict


a: defaultdict[str, list] = defaultdict(list)


a["gello"].extend([1,2, 3])

print(a)