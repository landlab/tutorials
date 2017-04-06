#! /usr/bin/env python
from __future__ import print_function

import os
import sys
import argparse
import tempfile
import subprocess
import re
from fnmatch import fnmatch

import six

from scripting.unix import system, check_output
from scripting.contexts import cd
from scripting.prompting import success, error, status


def convert_notebook(notebook):
    script = check_output(['jupyter', 'nbconvert', '--to', 'python',
                           '--stdout', notebook])

    p = re.compile(b"^get_ipython\(\)\.magic\(u?'matplotlib (?P<magic>\w+)'\)",
                   re.MULTILINE)
    script = p.sub(b"get_ipython().magic(u'matplotlib auto')", script)
    p = re.compile(b"(?P<magic>^get_ipython\(\)\.magic\(u'pinfo[\w\s]+'\))",
                   re.MULTILINE)
    script = p.sub(b"# \\1", script)

    return script


def run_notebook(notebook):
    with cd(os.path.dirname(notebook)):
        script = convert_notebook(os.path.basename(notebook))
        _, script_file = tempfile.mkstemp(prefix='.', suffix='.py', dir='.')
        with open(script_file, 'wb') as fp:
            fp.write(script)
        try:
            subprocess.check_call(['ipython', script_file])
        except Exception:
            raise
        finally:
            os.remove(script_file)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('notebook', type=str, nargs='+',
                        help='Notebook to test.')
    parser.add_argument('--skip', type=str, action='append',
                        help='Notebooks to skip.')

    args = parser.parse_args()

    skip = set()
    for pattern in args.skip:
        skip |= set([nb for nb in args.notebook if fnmatch(nb, pattern)])

    summary = []
    for notebook in args.notebook:
        if notebook in skip:
            summary.append((notebook, 'SKIP'))
            status('SKIP: ' + notebook)
        else:
            try:
                run_notebook(notebook)
            except subprocess.CalledProcessError:
                summary.append((notebook, 'FAIL'))
                error(notebook)
            else:
                summary.append((notebook, 'PASS'))
                success(notebook)

    print('-' * 70)
    print('Summary:')
    for notebook, result in summary:
        if result == 'FAIL':
            error(notebook)
        elif result == 'PASS':
            success(notebook)
        elif result == 'SKIP':
            status('SKIP: ' + notebook)
    print('-' * 70)

    failures = [name for name, result in summary if result == 'FAIL']
    passes = [name for name, result in summary if result == 'PASS']

    if failures:
        print('FAILED (failures={nfails})'.format(nfails=len(failures)))
    else:
        print('OK Ran {ntests} tests'.format(ntests=len(passes)))

    return len(failures)


if __name__ == '__main__':
    sys.exit(main())
