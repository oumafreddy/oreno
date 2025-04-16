import os

def print_tree(startpath, indent=""):
    for item in os.listdir(startpath):
        path = os.path.join(startpath, item)
        if os.path.isdir(path):
            print(f"{indent}|-- {item}")
            print_tree(path, indent + "    ")
        else:
            print(f"{indent}|-- {item}")

if __name__ == "__main__":
    project_root = '.'  # change this path if needed
    print_tree(project_root)
