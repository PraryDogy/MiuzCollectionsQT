max_row = 25
name = "R01-FST-0193_R01-FST-0184_R01-FST-0190.jpg"
name = f"Filename: {name}"

if len(name) >= max_row * 2:
    cut_name = name[:max_row * 2]
    cut_name = cut_name[:-6]
    name = cut_name + "..." + name[-3:]

name = name[:max_row] + "\n" + name[max_row:]

print(name)