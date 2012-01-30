#!/bin/bash

cd "$( dirname "$0" )"

while :; do
    inotifywait -r -e modify,close_write,moved_to,moved_from,move,create,delete ../
    make html
done
