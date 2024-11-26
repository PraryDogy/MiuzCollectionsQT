class Test:
    def __init__(self):
        super().__init__()

        self.row = 0
        self.col = 0

a = Test()

coords = (4, 4)
a.row, a.col = coords

print(a.row, a.col)