import re

with open("styles/dark_theme.css", "r") as file:
    d_theme = file.read()

with open("styles/light_theme.css", "r") as file:
    l_theme = file.read()


def remove_comments(css_text):
    # Регулярное выражение для удаления комментариев
    pattern = r'/\*.*?\*/'
    return re.sub(pattern, '', css_text, flags=re.DOTALL)


def split_css_blocks(css_text):
    # Удаляем комментарии
    css_text = remove_comments(css_text)
    
    # Регулярное выражение для поиска блоков стилей
    pattern = r'([^\s{}][^{}]*?\{[^{}]*\})'
    blocks = re.findall(pattern, css_text, re.DOTALL)
    return blocks


def extract_and_sort_id_selectors(blocks):
    id_selectors = []
    other_selectors = []
    
    for block in blocks:
        selector = block.split('{')[0].strip()
        if selector.startswith("#"):
            id_selectors.append(block)
        else:
            other_selectors.append(block)
    
    # Сортируем блоки с селекторами, начинающимися с #
    id_selectors.sort(key=lambda x: x.split('{')[0].strip())
    
    return id_selectors, other_selectors

def save_sorted_css(id_selectors, other_selectors, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        for block in id_selectors:
            f.write(block + '\n\n')
        
        for block in other_selectors:
            f.write(block + '\n\n')

output_css_path = 'sorted_output.css'
css_blocks = split_css_blocks(d_theme)
id_selectors, other_selectors = extract_and_sort_id_selectors(css_blocks)
save_sorted_css(id_selectors, other_selectors, output_css_path)
