class Test:

    def __init__(self):
        super().__init__()
        self.paths = [1, 2, 3, 4, 555]

    @property
    def path(self):
        return self.paths[-1]

    @path.setter
    def path(self, value):
        self.paths[-1] = value


test = Test()
test.path = "dafvsadfds"
print(test.path)  # dafvsadfds