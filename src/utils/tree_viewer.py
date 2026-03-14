import os
from pathlib import Path

def print_tree(directory, prefix="", ignore_list=None, empty_dirs=None):
    if ignore_list is None:
        ignore_list = {'.git', '__pycache__', 'venv', '.venv', 'env', '.idea', '.vscode'}
    if empty_dirs is None:
        # Pastas que queremos mostrar, mas não listar o que tem dentro
        empty_dirs = {'data'}
    
    paths = sorted(Path(directory).iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    # Filtra as pastas de sistema/ignore
    paths = [p for p in paths if p.name not in ignore_list and not p.name.startswith('.')]
    
    for i, path in enumerate(paths):
        is_last = (i == len(paths) - 1)
        connector = "└── " if is_last else "├── "
        
        print(f"{prefix}{connector}{path.name}{'/' if path.is_dir() else ''}")
        
        # Se for um diretório e NÃO estiver na lista de pastas para ignorar o conteúdo
        if path.is_dir() and path.name not in empty_dirs:
            new_prefix = prefix + ("    " if is_last else "│   ")
            print_tree(path, new_prefix, ignore_list, empty_dirs)

if __name__ == "__main__":
    # Pega o nome da pasta atual para o topo da árvore
    print(f"{os.path.basename(os.getcwd())}/")
    print_tree('.')