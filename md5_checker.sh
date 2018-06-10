#!/bin/bash
FILE=$1
python lt_codes.py $FILE --systematic
md5sum.exe "${FILE}"
md5sum.exe "${FILE%%.*}-copy.${FILE#*.}"