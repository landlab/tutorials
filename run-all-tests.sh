#! /bin/bash

EXCLUDES="--exclude=*intro*" # krb note: as best as I can tell this is only supposed to skip the tutorial python_intro/Python_intro.ipynb

./run_notebook.py find . | ./run_notebook.py run --file=- $EXCLUDES
