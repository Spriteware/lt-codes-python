# Fountain Code: Efficient Python Implementation of LT Codes

This project is the implementation in Python of the iterative encoding and iterative decoding algorithms of the [LT Codes](https://en.wikipedia.org/wiki/LT_codes),
an error correction code based on the principles of [Fountain Codes](https://en.wikipedia.org/wiki/Fountain_code) by Michael Luby.
I have written a whole article on LT Codes and this snippet that you can find here : [franpapers.com](https://franpapers.com/en/algorithmic/2018-introduction-to-fountain-codes-lt-codes-with-python/)

The encoder and decoder are optimized to handle big transfers for files between 1MB to 1GB at high speed.

### Installation

This implementation requires at least python 3.x.
Some packages are not built-in. To install them with `pip` you can do:

```
$ pip install -r requirements.txt
```

## Usage

An example describing how to use the implementation is in `lt_codes.py`, and you can use it to encode/decode a file on the fly (creates a file copy):
```
$ python lt_codes.py filename [-h] [-r REDUNDANCY] [--systematic] [--verbose] [--x86]
```

As an example, here is a basic test to ensure the integrity of the final file:
```
$ echo "Hello!" > test.txt
$ python lt_codes.py test.txt --systematic
```
A new file test-copy.txt should be created with the same content.

### Content

* `core.py` contains the Symbol class, constants and functions that are used in both encoding and decoding.
* `distributions.py` contains the two functions that generate degrees based on the ideal soliton and robust soliton distributions
* `encoder.py` contains the encoding algorithm
* `decoder.py` contains the decoding algorithm
* `md5_checker.sh` calls `lt_codes.py` and then compare the integrity of the original file with the newly created file. The integrity check is made with `md5sum`, add the ".exe" if you work on Window. Replace it by `md5 -r` if you work on Mac, or run `brew install md5sha1sum`.

## Benchmarks
The time consumed by the encoding and decoding process is completely related to the size of the file to encode and the wanted redundancy.
I have made some measure on an Intel i5 @ 2.30GHz with a 1.5 redundancy :

<table>
<thead>
<tr>
<td rowspan="2"><strong>Size (MB)</strong></td>
<td rowspan="2"><strong>Blocks</strong></td>
<td rowspan="2"><strong>Symbols</strong></td>
<td colspan="2"><strong>Encoding</strong></td>
<td colspan="2"><strong>Decoding</strong></td>
</tr>
<tr>
<td><strong>Time (s)</strong></td>
<td><strong>Speed (MB/s)</strong></td>
<td><strong>Time (s)</strong></td>
<td><strong>Speed (MB/s)</strong></td>
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

Note: `PACKET_SIZE` is set to 65536 for theses tests. Lowering it will result in lower speeds but it might be necessary it to send small files in many chunks.


## References

> M.Luby, "LT Codes", The 43rd Annual IEEE Symposium on Foundations of Computer Science, 2002.

## License

MIT License
Copyright (c) 2018 François Andrieux

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

