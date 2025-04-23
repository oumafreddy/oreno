import os

def tree(dir_path, prefix=""):
    contents = list(os.listdir(dir_path))
    contents.sort()
    pointers = ['+-- '] * (len(contents) - 1) + ['+-- ']
    for pointer, name in zip(pointers, contents):
        path = os.path.join(dir_path, name)
        print(prefix + pointer + name)
        if os.path.isdir(path):
            extension = '|   ' if pointer == '+-- ' else '    '
            tree(path, prefix + extension)

if __name__ == "__main__":
    root_dir = "."
    print("oreno/")
    tree(root_dir)
