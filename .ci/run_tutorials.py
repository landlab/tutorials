from __future__ import print_function

import os
import importlib
import subprocess
from glob import glob


THIS_DIR = os.path.abspath(os.path.dirname(__file__))


def find_tutorials(basedir):
    return glob(os.path.join(basedir, '**/*.py'))


def run_tutorials(paths):
    for path in paths:
        run_tutorial(path)


def run_tutorial(path):
    here = os.path.abspath(os.getcwd())

    (dirname, script) = os.path.split(path)
    os.chdir(dirname)

    header = os.path.join(THIS_DIR, 'header.txt')

    cat = ['cat', header, script]
    try:
        print('{name}: running tutorial'.format(name=script))
        proc = subprocess.Popen(cat, stdout=subprocess.PIPE)
        with open('stdout.txt', 'w') as fp:
            subprocess.Popen(['python'], stdin=proc.stdout, stdout=fp)
    except ImportError:
        print('{name}: unable to run tutorial'.format(name=script))
    else:
        print('{name}: success'.format(name=script))
    finally:
        os.chdir(here)


def main():
    run_tutorials(find_tutorials('.'))


if __name__ == '__main__':
    main()
