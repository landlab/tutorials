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
    with cd(os.path.dirname(notebook) or '.'):
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


def print_summary(summary):
    print('-' * 70)
    for notebook, result in summary:
        if result is None:
            status('SKIP: ' + notebook)
        elif result:
            success(notebook)
        else:
            error(notebook)
    print('-' * 70)


def print_success_or_failure(summary):
    failures = [name for name, result in summary if result is False]
    passes = [name for name, result in summary if result is True]

    if failures:
        print('FAILED (failures={nfails})'.format(nfails=len(failures)))
    else:
        print('OK Ran {ntests} tests'.format(ntests=len(passes)))

    return len(failures)


def check_notebook(notebook, dry_run=False):
    try:
        dry_run or run_notebook(notebook)
    except subprocess.CalledProcessError:
        return False
    else:
        return True


def match_by_pattern(strings, patterns):
    """Match strings by patterns.

    Parameters
    ----------
    strings : iterable of str
        Collection of strings.
    patterns : iterable of str
        List of glob-style patterns to remove.

    Returns
    -------
    list of str
        All strings that match any of the patterns.
    """
    def string_matches_one_of(string, patterns):
        for pattern in patterns:
            if fnmatch(string, pattern):
                return True
        return False

    matches = []
    for string in strings:
        if string_matches_one_of(string, patterns):
            matches.append(string)

    return matches


def read_notebooks_from_file(file_like):
    if file_like:
        return [nb.strip() for nb in file_like if nb.strip()]
    else:
        return []


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='Run Jupyter notebooks.')
    parser.add_argument('notebook', type=str, nargs='*', default=[],
                        help='Notebook to test.')
    parser.add_argument('-e', '--exclude', metavar='PATTERN', type=str,
                        action='append', default=[],
                        help='Notebooks to exclude.')
    parser.add_argument('--dry-run', action='store_true',
                        help='Find notebooks but do not do anything')
    parser.add_argument('-f', '--file', type=argparse.FileType('r'),
                        help='Read notebooks from a file.')

    args = parser.parse_args()

    notebooks = read_notebooks_from_file(args.file) + args.notebook

    excluded = match_by_pattern(notebooks, args.exclude)

    summary = []
    for notebook in notebooks:
        if notebook in excluded:
            result = notebook, None
        else:
            result = notebook, check_notebook(notebook, dry_run=args.dry_run)
        print_summary([result])
        summary.append(result)

    print_summary(summary)
    return print_success_or_failure(summary)


if __name__ == '__main__':
    sys.exit(main())
