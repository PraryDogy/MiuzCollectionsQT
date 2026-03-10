
def check(x: int, y: int):
    



    if x > 0 and y > 0:
        return 1
    elif x < 0 and y > 0:
        return 2
    elif x < 0 and y < 0:
        return 3
    elif x > 0 and y < 0:
        return 4
    else:
        return None


counters = {
    1: {"name": "Первая четверть", "count": 0},
    2: {"name": "Вторая четверть", "count": 0},
    3: {"name": "Третья четверть", "count": 0},
    4: {"name": "Четвертая четверть", "count": 0},
}

count = int(input())
for i in range(1, count + 1):
    try:
        x, y = map(int, input().split())
        res = check(x, y)
        if res:
            counters[res]["count"] += 1
    except Exception:
        break

for v in counters.values():
    text = f'{v["name"]}: {v["count"]}'
    print(text)
