# Fountain Code: Efficient Python Implementation of LT Codes

This project is the implementation in Python of the iterative encoding and iterative decoding algorithms of the [LT Codes](https://en.wikipedia.org/wiki/LT_codes), 
an error correction code based on the principles of [Fountain Codes](https://en.wikipedia.org/wiki/Fountain_code).
I have wrote a whole article on LT Codes and this snippets that you can find here : [franpapers.com](franpapers.com)

The encoder and decoder are optimized to handle big transfers for files between 1MB to 1GB at high speed.

## How to use it

Usage (python 3.x):
```
python lt_codes.py filename [-h] [-r REDUNDANCY] [--systematic] [--verbose] [--x86]
```

An example describing how to use the implementation is in `lt_codes.py`. However:
* `core.py` contains the Symbol class, constants and functions that are used in both encoding and decoding.
* `distributions.py` contains the two functions that generate degrees based on the ideal soliton and robust soliton distributions
* `encoder.py` contains the encoding algorithm
* `decoder.py` contains the decoding algorithm
* `md5_checker.sh` calls `lt_codes.py` and then compare the integrity of the original file with the newly created file. The integrity check is made with `md5sum.exe`, remove the ".exe" if you work on Unix.

## Benchmarks
The time consumed by the encoding and decoding process is completely related to the size of the file to encode and the wantedd redundancy.
I have made some measure on a Intel i5 @ 2.30GHz with a 1.5 redundancy : 

<table>
<thead>
<tr>
<td rowspan="2"><strong>Taille (MB)</strong></td>
<td rowspan="2"><strong>Blocs</strong></td>
<td rowspan="2"><strong>Symboles</strong></td>
<td colspan="2"><strong>Encodage</strong></td>
<td colspan="2"><strong>Décodage</strong></td>
</tr>
<tr>
<td><strong>Temps (s)</strong></td>
<td><strong>Vitesse (MB/s)</strong></td>
<td><strong>Temps (s)</strong></td>
<td><strong>Vitesse (MB/s)</strong></td>
</tr>
</thead>
<tbody>
<tr>
<td>1</td>
<td>16</td>
<td>24</td>
<td>0.00</td>
<td>-</td>
<td>0.00</td>
<td>-</td>
</tr>
<tr>
<td>100</td>
<td>1600</td>
<td>2400</td>
<td>0.21</td>
<td>476.1</td>
<td>0.31</td>
<td>322.5</td>
</tr>
<tr>
<td>1200</td>
<td>19200</td>
<td>28800</td>
<td>3.86</td>
<td>310.8</td>
<td>39.82</td>
<td>30.1</td>
</tr>
<tr>
<td>2000</td>
<td>32000</td>
<td>48000</td>
<td>6.44</td>
<td>310.5</td>
<td>104.10</td>
<td>19.2</td>
</tr>
<tr>
<td>3600</td>
<td>57600</td>
<td>86400</td>
<td>23.14</td>
<td>155.5</td>
<td>426.36</td>
<td>8.4</td>
</tr>
</tbody>
</table>

<img src="https://franpapers.com/wp-content/uploads/2018/06/word-image-18.png" width=500 />
