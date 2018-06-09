#!/bin/bash

# Sizes: 100B, 100KB, 100MB, 400MB
for SIZE in 100 102400 104857600 419430400
do
    echo -e "\nCreating dummy data for size=$SIZE"
    echo "======================================"
    head -c $SIZE /dev/urandom > dummy
    python lt_codes.py dummy --systematic
done