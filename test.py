class Item:
    def __init__(self, size, mod, created):
        self.size: int = size
        self.mod: int = mod
        self.created: int = created


items = []
for i in range(0, 10):
    item_ = Item(i, i, i)
    items.append(item_)


test = Item(3, 3, 3)

if test in items:
    print(1)