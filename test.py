from lang import Lng


# class LngRus(Lng):
#     def __getattribute__(self, item):
#         return getattr(Lng, item)[0]
#         # value = super().__getattribute__(item)
#         # if isinstance(value, list):
#             # return value[0]  # Возвращает элемент с индексом 0
#         # return value


# # Пример использования:
# lng_rus = LngRus()
# print(lng_rus.add_fav)  # Выведет: "Добавить в избранное"
# print(lng_rus.apply)    # Выведет: "Применить"

print(Lng.type_)