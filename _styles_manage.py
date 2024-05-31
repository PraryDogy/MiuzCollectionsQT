import re

with open("styles/dark_theme.css", "r") as file:
    d_theme = file.read()

with open("styles/light_theme.css", "r") as file:
    l_theme = file.read()


def css_dict(css: str):
    comments = r"(/\*.+\*/)"
    css = re.sub(comments, "", css)

    selectors_list = r'(\S+\s*\{[^}]*\})'
    selectors_list = re.findall(selectors_list, css, re.DOTALL)

    if not selectors_list:
        return

    css_dict = {}

    for selector in selectors_list:

        pattern = r'(\S+\s*)\{'
        re_name = re.findall(pattern, selector)

        if re_name:
            re_name = re_name[0].strip()
            selector = selector.replace(re_name, "")
        else:
            continue

        pattern = r"([a-zA-Z\-]+)\s*:\s*([^;]+);"
        re_props = re.findall(pattern, selector)

        if re_props:
            re_props = [
                {prop_name: prop_val}
                for prop_name, prop_val in re_props
                ]
        else:
            continue

        css_dict[re_name] = re_props

    return css_dict


def to_css(css_dict: dict, filename: str):
    css_dict = dict(sorted(css_dict.items()))

    css_text = ""

    # Проход по каждой паре ключ-значение в словаре
    for selector, properties in css_dict.items():
        css_text += f"{selector} {{\n"
        
        # Проход по списку свойств для текущего селектора
        for prop in properties:
            for key, value in prop.items():
                css_text += f"    {key}: {value};\n"
        
        css_text += "}\n\n"

    # Запись CSS-текста в файл
    with open(f"{filename}.css", "w") as f:
        f.write(css_text)


def compare_dicts(dict1: dict, dict2: dict, dict1_name: str, dict2_name: str):
    for selector, properties in dict1.items():

        if selector in dict2:

            properties_dict1 = {
                list(prop.keys())[0]: list(prop.values())[0]
                for prop in properties
                }

            properties_dict2 = {
                list(prop.keys())[0]: list(prop.values())[0]
                for prop in dict2[selector]
                }
            
            missing_properties = set(
                properties_dict1.keys()) - set(properties_dict2.keys()
                                               )
            
            if missing_properties:
                print(f"Есть в ---{dict1_name}---, нет в ---{dict2_name}---")
                print(f"{selector}")
                for prop in missing_properties:
                    print(f"{prop}: {properties_dict1[prop]}")
                print()


l_theme = css_dict(l_theme)
d_theme = css_dict(d_theme)

print()
print("Нажмите 1, если хотите обновить и упорядочить css файлы")
print("Нажмите 2, если хотите узнать, каких селекторов не хватает в css")
print("Нажмите 3, если хотите узнать, каких свойств селекторов не хватает")
print("Нажмите 4, чтобы сравнить селекторы в styles.main --> Names и css")
print()

inp = input()

if inp == "1":
    to_css(l_theme, "light_theme")
    to_css(d_theme, "dark_theme")

elif inp == "2":
    keys_only_in_A = set(l_theme.keys()) - set(d_theme.keys())
    keys_only_in_B = set(d_theme.keys()) - set(l_theme.keys())
    print()
    print("Есть в ---light_theme---, нет в ---dark theme---:")
    print(keys_only_in_A)
    print()
    print("Есть в ---dark_theme---, нет в ---light_theme---:")
    print(keys_only_in_B)
    print()

elif inp == "3":
    print()
    compare_dicts(l_theme, d_theme, "light_theme", "dark_theme")
    print("--------")
    compare_dicts(d_theme, l_theme, "dark_theme", "light")
    print()


elif inp == "4":
    from styles.main import Names

    names = {
        i
        for i in Names.__dict__.values()
        if type(i) == str
        }
    
    names_l_theme = {
        i.replace("#", "")
        for i in l_theme.keys()
        if i.startswith("#")
        }
    
    names_d_theme = {
        i.replace("#", "")
        for i in l_theme.keys()
        if i.startswith("#")
        }
    
    names.remove("styles.main")
    names = set(sorted(names))
    names_l_theme = set(sorted(names_l_theme))
    names_d_theme = set(sorted(names_d_theme))

    if names > names_l_theme:
        print()
        print("Есть в main.py и нет в light_theme.css:")
        print(names - names_l_theme)
    else:
        print()
        print("Есть в light_theme.css и нет в main.py:")
        print(names_l_theme - names)

    print()
    print("------")
    print()

    if names > names_d_theme:
        print("Есть в main.py и нет в dark_theme.css:")
        print(names - names_d_theme)
    else:
        print()
        print("Есть в dark_theme.css и нет в main.py:")
        print(names_d_theme - names)
    
    print()