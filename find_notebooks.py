#! /usr/bin/env python
from __future__ import print_function

import os
from six.moves import shlex_quote


def find_notebooks(base):
    """Find Jupyter notebooks.

    Parameters
    ----------
    base : str
        Path to search for notebooks under.

    Returns
    -------
    list of str
        Paths to discovered notebooks.
    """
    notebooks = []
    for root, dirs, files in os.walk(base, topdown=True):
        for dir in dirs:
            if dir.startswith('.'):
                dirs.remove(dir)
        for fname in files:
            file_path = os.path.join(root, fname)
            if file_path.endswith('.ipynb'):
                notebooks.append(file_path)
    return notebooks


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='Find Jupyter notebooks under a given base path')
    parser.add_argument('path', help='Path to search for notebooks.')
    parser.add_argument('--sort', action='store_true',
                        help='Sort notebooks alphabetically.')

    args = parser.parse_args()

    notebooks = find_notebooks(args.path)

    if args.sort:
        notebooks.sort()

    # print(os.linesep.join([shlex_quote(nb) for nb in notebooks]))
    print(os.linesep.join([nb for nb in notebooks]))


if __name__ == '__main__':
    main()
