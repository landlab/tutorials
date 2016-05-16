from __future__ import print_function

import os
import sys
import importlib
import subprocess
from glob import glob
import collections


THIS_DIR = os.path.abspath(os.path.dirname(__file__))


def find_tutorials(basedir):
    return glob(os.path.join(basedir, '**/*.py'))


def run_tutorials(paths):
    status = collections.defaultdict(list)
    for path in paths:
        try:
            print('{name}: running tutorial'.format(name=path))
            run_tutorial(path)
        except subprocess.CalledProcessError:
            print('{name}: unable to successfully run tutorial'.format(
                name=path))
            status['fail'].append(path)
        else:
            status['pass'].append(path)
            print('{name}: success'.format(name=path))

    return status


def run_tutorial(path):
    here = os.path.abspath(os.getcwd())

    (dirname, script) = os.path.split(path)
    os.chdir(dirname)

    header = os.path.join(THIS_DIR, 'header.txt')

    cat = ['cat', header, script]
    try:
        proc = subprocess.Popen(cat, stdout=subprocess.PIPE)
        with open('stdout.out', 'w') as fp:
            subprocess.check_call(['python'], stdin=proc.stdout, stdout=fp)
    except subprocess.CalledProcessError:
        raise
    finally:
        os.chdir(here)


def main():
    errors = run_tutorials(find_tutorials('.'))

    try:
        print(errors['fail'])
    except KeyError:
        sys.exit(0)
    else:
        sys.exit(-1)


if __name__ == '__main__':
    main()
