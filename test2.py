collfolders: list[list[str]] = [
    # miuz coll folders
    [
        '/Volumes/Shares/Studio/MIUZ/Photo/Art/Ready',
        '/Volumes/Shares-1/Studio/MIUZ/Photo/Art/Ready',
        '/Volumes/Shares-2/Studio/MIUZ/Photo/Art/Ready',
    ],
    # panacea coll folders
    [
        '/Volumes/Shares/Studio/Panacea/Photo/Art/Ready',
        '/Volumes/Shares-1/Studio/Panacea/Photo/Art/Ready',
        '/Volumes/Shares-2/Studio/Panacea/Photo/Art/Ready',
        ]
]



stopcolls: list[list[str]] = [
    [
        "_Archive_Commerce_Брендинг",
        "Chosed",
        "LEVIEV"
    ],
    [], 
]

BRANDS = ["miuz", "panacea", "new"]


assert len(BRANDS) == len(stopcolls) == len(collfolders)