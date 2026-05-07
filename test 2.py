from system.items import ScanerDirItem

total = 5

finder_dirs = [
    ScanerDirItem("abs path", "rel_path", 123)
    for i in range(total)
]
finder_dirs = [
    f"{i.abs_path}, {i.rel_path}"
    for i in finder_dirs
]

removed_dirs = [
    ScanerDirItem("abs path", "rel_path", 123)
    for i in range(total)
]
removed_dirs = [
    f"{i.abs_path}, {i.rel_path}"
    for i in removed_dirs
]

lines = (
    "Удаление директорий:",
    f"finder dirs: {len(finder_dirs)}",
    f"removed dirs: {len(removed_dirs)}",
    "",
    "Список finder dirs (абсолютный путь, относительный путь)",
    *finder_dirs,
    "",
    "Список removed dirs (абсолютный путь, относительный путь)",
    *removed_dirs
)


text = "\n".join(lines)
print(text)
