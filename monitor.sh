#!/bin/bash
until python3 Main.py; do
    echo "'Bot' crashed with exit code $?. Restarting..." >&2
    sleep 1
done
