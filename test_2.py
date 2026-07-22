paths_list = [
    # Первая цепочка (Users)
    "/Users/Downloads/Documents",
    "/Users/Downloads/Documents/Projects",
    "/Users/Downloads/Documents/Projects/Python",
    "/Users/Downloads/Documents/Projects/Python/Scripts",
    "/Users/Downloads/Documents/Projects/Python/Scripts/Logs",
    
    # Вторая цепочка (Volumes)
    "/Volumes/Shares/Folder",
    "/Volumes/Shares/Folder/Archive",
    "/Volumes/Shares/Folder/Archive/2026",
    "/Volumes/Shares/Folder/Archive/2026/Reports",
    "/Volumes/Shares/Folder/Archive/2026/Reports/Financial"
]


def filter_top_level_paths(paths: list[str]):
    sorted_paths = sorted(paths)
    top_level = []
    for path in sorted_paths:
        if not top_level or not path.startswith(top_level[-1] + "/"):
            top_level.append(path)
    return top_level


result = filter_top_level_paths(paths_list)
for i in result:
    print(i)