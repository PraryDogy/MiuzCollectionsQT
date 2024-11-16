import os
import ast

exclude = ["env", "__pycache__"]

def get_functions_from_files(directory):
    functions = set()
    
    for root, dirs, files in os.walk(directory):

        dirs[:] = [d for d in dirs if d not in exclude]

        for file in files:
            if file.endswith('.py'):
                with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read(), filename=file)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            functions.add(node.name)
    return functions

def check_function_usage(directory, functions):
    used_functions = set()
    
    for root, dirs, files in os.walk(directory):

        dirs[:] = [d for d in dirs if d not in exclude]

        for file in files:
            if file.endswith('.py'):
                with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read(), filename=file)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                            if node.func.id in functions:
                                used_functions.add(node.func.id)
    
    unused_functions = functions - used_functions
    return unused_functions

directory_path = os.path.dirname(__file__)
all_functions = get_functions_from_files(directory_path)
# unused_functions = check_function_usage(directory_path, all_functions)

# print("Неиспользованные функции:")
# for func in unused_functions:
    # print(func)

print(all_functions)