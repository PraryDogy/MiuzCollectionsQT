with open("styles/dark_theme.css", "r") as file:
    dark_theme_selectors = file.readlines()
    dark_theme_selectors = [
        i.replace("{", "").strip()
        for i in dark_theme_selectors
        if i.startswith("#")
        ]

with open("styles/light_theme.css", "r") as file:
    light_theme_selectors = file.readlines()
    light_theme_selectors = [
        i.replace("{", "").strip()
        for i in light_theme_selectors
        if i.startswith("#")
        ]

print(len(dark_theme_selectors))
print(len(light_theme_selectors))