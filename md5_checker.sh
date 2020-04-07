#!/bin/bash
FILE=$1
python lt_codes.py $FILE --systematic
md5sum "${FILE}"
md5sum "${FILE%%.*}-copy.${FILE#*.}"