import os

# directories to skip entirely
SKIP_DIRS = {'.venv', '__pycache__', 'migrations', '.git'}

def tree(dir_path, prefix=""):
    """Recursively print a directory tree, filtering and counting files."""
    try:
        entries = sorted(os.listdir(dir_path))
    except PermissionError:
        return

    # filter out skip-dirs
    entries = [e for e in entries
               if e not in SKIP_DIRS
               and not e.startswith('.')]
    
    files = [e for e in entries if os.path.isfile(os.path.join(dir_path, e))]
    dirs  = [e for e in entries if os.path.isdir (os.path.join(dir_path, e))]

    # print files with counts
    for i, fname in enumerate(files):
        pointer = '├── ' if i < len(files)-1 or dirs else '└── '
        print(prefix + pointer + fname)

    # recurse into subdirs
    for i, dname in enumerate(dirs):
        pointer = '├── ' if i < len(dirs)-1 else '└── '
        full_path = os.path.join(dir_path, dname)
        # show folder and file count
        count = sum(len(fns) for _, _, fns in os.walk(full_path))
        print(prefix + pointer + f"{dname}/ ({count} files)")
        extension = '│   ' if i < len(dirs)-1 else '    '
        tree(full_path, prefix + extension)

if __name__ == "__main__":
    print("oreno/")
    tree("oreno")
