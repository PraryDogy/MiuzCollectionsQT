class Test:

    def __init__(self):
        super().__init__()
        self.paths = [1, 2, 3, 4, 555]

    @property
    def path(self):
        return self.paths[-1]


test = Test()
print(test.path)