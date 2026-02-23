import os
import sys


def strip_conflicts(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    new_lines = []
    in_conflict = False
    keep_ours = False

    for line in lines:
        if line.startswith('<<<<<<<'):
            in_conflict = True
            keep_ours = True
            continue
        elif line.startswith('======='):
            keep_ours = False
            continue
        elif line.startswith('>>>>>>>'):
            in_conflict = False
            keep_ours = False
            continue

        if not in_conflict or keep_ours:
            new_lines.append(line)

    with open(filepath, 'w') as f:
        f.writelines(new_lines)

if __name__ == "__main__":
    for arg in sys.argv[1:]:
        if os.path.isfile(arg):
            strip_conflicts(arg)
