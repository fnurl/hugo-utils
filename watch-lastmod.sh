#!/bin/bash

# watch for changes in .md files in the content directory. If a change is found,
# run update-lastmod. Wait 1 seconds between checks.
#
# requires fswatch (install via homebrew) and update-lastmod.py 
# in path (avialable from https://github.com/fnurl/hugo-utils)

EXPECTED_ARGS=1
WATCH_DIR="."
if [ "$#" -ne $EXPECTED_ARGS ]; then
  echo "Path missing. Using current dir. "
else
    WATCH_DIR=$1
fi
echo "Watching $WATCH_DIR/*.md. Will run update-lastmod.py on file updates."

while :
do
    # -0 use NUL char as delimiter, -1 one event then quit, -r recursive, -L follow symlinks
    # regex for .md-files, only on update events (i.e. not created and removed etc)
    fswatch -0 -1 -r -L --include=".*\.md" --event Updated $WATCH_DIR | xargs -0 -t -n 1 update-lastmod.py
    sleep 1
done
