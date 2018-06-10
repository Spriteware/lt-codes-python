#!/bin/bash

# Sizes: 100B, 100KB, 1MB, 100MB, 400MB, 800MB, 1.17GB, 1.56GB, 1.95GB, 2.34GB, 2.73GB, 3.51GB
sizes="100 102400 1048576 104857600 419430400 838860800 1258291200 1264867868 2097152000 2516582400 2931315179 3774873600"
for SIZE in $sizes
do
    echo -e "\nCreating dummy data for size=$SIZE"
    echo "======================================"
    echo "" > benchmark.log
    head -c $SIZE /dev/urandom > dummy
    python ../lt_codes.py dummy -r 1.5 --systematic
done

rm dummy
rm dummy-copy
