test: list[dict] = [
    {
        "fake_name": "Naomi",
        "true_name": "11 Naomi"
    },
    {
        "fake_name": "Aiogram",
        "true_name": "20 Aiogram"
    },
]


test = sorted(
    test,
    key=lambda x: x["fake_name"]
    )

print(test)