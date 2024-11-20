json_filtres = (
    (('Продукт', 'Product'), '1 IMG', False),
    (('Модели', 'Model'), '2 MODEL IMG', False),
    (('Остальное', 'Other'), 'other_flag', False)
    )

class Filter:
    current: list["Filter"] = []
    __slots__ = ["names", "real", "value"]

    def __init__(self, names: list, real: str, value: bool):

        self.names = names
        self.real = real
        self.value = value

    def get_data(self):
        return (self.names, self.real, self.value)
    

for i in json_filtres:
    Filter.current.append(Filter(*i))

for i in Filter.current:
    print(i.get_data())