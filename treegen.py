import os

# directories to skip entirely
SKIP_DIRS = {'.venv', '__pycache__', 'migrations', '.git'}

def tree(dir_path, prefix="", max_depth=2, level=0):
    """Recursively print a leaner tree, limited by max_depth."""
    if level >= max_depth:
        return

    try:
        entries = sorted(os.listdir(dir_path))
    except PermissionError:
        return

    # filter out unwanted entries
    entries = [e for e in entries if e not in SKIP_DIRS and not e.startswith('.')]
    files = [e for e in entries if os.path.isfile(os.path.join(dir_path, e))]
    dirs  = [e for e in entries if os.path.isdir(os.path.join(dir_path, e))]

    # print files in current dir
    for i, fname in enumerate(files):
        pointer = '├── ' if i < len(files)-1 or dirs else '└── '
        print(prefix + pointer + fname)

    # recurse into subdirs (with file counts)
    for i, dname in enumerate(dirs):
        pointer = '├── ' if i < len(dirs)-1 else '└── '
        full_path = os.path.join(dir_path, dname)

        # count all files inside this folder (recursively)
        count = sum(len(files) for root, dirs, files in os.walk(full_path) 
                    if os.path.basename(root) not in SKIP_DIRS)

        print(prefix + pointer + f"{dname}/ ({count} files)")
        extension = '│   ' if i < len(dirs)-1 else '    '
        tree(full_path, prefix + extension, max_depth, level+1)

if __name__ == "__main__":
    root = os.getcwd()  # current folder
    print(os.path.basename(root) + "/")
    tree(root, max_depth=2)   # adjust max_depth
