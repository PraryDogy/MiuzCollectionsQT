from database import Dbase, ThumbsMd
import sqlalchemy
from collections import defaultdict

Dbase.create_engine()


class CollItem:
    __slots__ = ["true_name", "short_name"]
    def __init__(self, true_name: str, short_name: str):
        self.true_name = true_name
        self.short_name = short_name


q = sqlalchemy.select(ThumbsMd.collection).distinct()
conn = Dbase.engine.connect()
res: list[str] = (i[0] for i in conn.execute(q).fetchall() if i)
conn.close()

collections = defaultdict(list)

for true_name in res:
    fake_name = true_name.lstrip("0123456789").strip()
    fake_name = fake_name if fake_name else true_name
    letter = fake_name[0].capitalize()

    collections[letter].append(CollItem(true_name, fake_name))

a = {
    key: sorted(value, key=lambda item: item.true_name)
    for key, value in sorted(collections.items())
    }

for letter, coll_item_list in a.items():
    for coll_item in coll_item_list:
        print(letter, coll_item.true_name, coll_item.short_name)