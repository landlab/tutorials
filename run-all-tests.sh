#! /bin/bash

EXCLUDES="--exclude=*intro* --exclude=*flow_direction*"

./run_notebook.py find . | ./run_notebook.py run --file=- $EXCLUDES
