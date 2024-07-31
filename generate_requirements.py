"""
Code to help generate requirements.txt faster.
It traverses the entire directory to find all python files and Jupyter Notebooks recursively.
Loads all python code as string
Parses it as ast node objects
Finds import statements and from import statements file-wise.
Computes what are locally python codes, removes them from requirement.txt
Checks for basic modules (inbuilt ones)
Writes to file.

It is Experimental and Work in Progress.

"""

import os
import ast
import json
import pkg_resources
import sys
import re

def get_imports_from_code_new(code):
    imports = set()
    import_pattern = re.compile(r'^\s*(?:import|from)\s+([a-zA-Z0-9_\.]+)', re.MULTILINE)
    matches = import_pattern.findall(code)
    for match in matches:
        module = match.split('.')[0]
        imports.add(module)
    return imports

def get_imports_from_code(code):
    tree = ast.parse(code)
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                imports.add(n.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)
    return imports

def get_imports_from_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            code = file.read()
    except UnicodeDecodeError:
        with open(filepath, 'r', encoding='latin-1') as file:
            code = file.read()
    return get_imports_from_code(code)

def get_imports_from_notebook(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            notebook = json.load(file)
    except UnicodeDecodeError:
        with open(filepath, 'r', encoding='latin-1') as file:
            notebook = json.load(file)
    imports = set()
    for cell in notebook.get('cells', []):
        if cell.get('cell_type') == 'code':
            code = ''.join(cell.get('source', ''))
            imports |= get_imports_from_code(code)
    return imports

def get_all_imports(directory):
    import_list = []
    all_imports = set()
    for root, _, files in os.walk(directory):
        for file in files:
            filepath = os.path.join(root, file)
            if file.endswith('.py'):
                all_imports |= get_imports_from_file(filepath)
                import_list.append([file, list(all_imports)])
            elif file.endswith('.ipynb'):
                all_imports |= get_imports_from_notebook(filepath)
                import_list.append([file, list(all_imports)])
    print("All Imports : ")
    for filename, imports in import_list:
        print("\nFILE : ", filename, "\n")
        for item in imports:
            print("\t", item)

    # return all_imports
    return import_list

def filter_packages(import_list):
    """
    This package will find the commonly called python scripts 
    apart from libraries and packages

    Input -> import_list = [filename, [list of imports]]

    """
    all_files = [i.split('.')[0].strip() for i, j  in import_list]
    all_imports = []
    for files, imports in import_list:
        for each_import in imports:
            if '.' in each_import:
                each_import = each_import.split('.')[0]  
                if each_import.strip() not in all_files:
                    all_imports.append(each_import)
            else:
                if each_import.strip() not in all_files:
                    all_imports.append(each_import)
    all_imports  = list(set(all_imports))
    all_imports = [i for i in all_imports if not is_standard_library(i) ]
    print("\nAll FInal Imports : \n")
    for i in all_imports:
        print("\t", i)

    
    return all_imports

def is_standard_library(module_name):
    if module_name in sys.builtin_module_names:
        return True
    return False
    # module_spec = importlib.util.find_spec(module_name)
    # return module_spec is None or 'site-packages' not in (module_spec.origin or '')

def map_imports_to_packages(imports):
    package_names = set()
    for imp in imports:
        if is_standard_library(imp):
            continue
        try:
            dist = pkg_resources.get_distribution(imp)
            package_names.add(f"{dist.project_name}=={dist.version}")
        except pkg_resources.DistributionNotFound:
            # If distribution is not found, you can log or handle it as needed
            print(f"Package for import '{imp}' not found.")
    return package_names

def write_requirements_file(packages, output_file='my_requirements.txt'):
    with open(output_file, 'w') as file:
        for package in sorted(packages):
            file.write(package + '\n')

def main(directory):
    import_list = get_all_imports(directory)
    filtered_packages = filter_packages(import_list)
    #packages = map_imports_to_packages(imports)
    write_requirements_file(filtered_packages)

if __name__ == "__main__":
    
    project_directory = input("Enter path to your project root directory: ")
    project_directory = os.path.abspath(project_directory)
    main(project_directory)
