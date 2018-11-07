#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import math
import argparse
import numpy as np
import core
from encoder import encode
from decoder import decode

def blocks_read(file, filesize):
    """ Read the given file by blocks of `core.PACKET_SIZE` and use np.frombuffer() improvement.

    Byt default, we store each octet into a np.uint8 array space, but it is also possible
    to store up to 8 octets together in a np.uint64 array space.  
    
    This process is not saving memory but it helps reduce dimensionnality, especially for the 
    XOR operation in the encoding. Example:
    * np.frombuffer(b'\x01\x02', dtype=np.uint8) => array([1, 2], dtype=uint8)
    * np.frombuffer(b'\x01\x02', dtype=np.uint16) => array([513], dtype=uint16)
    """

    blocks_n = math.ceil(filesize / core.PACKET_SIZE)
    blocks = []

    # Read data by blocks of size core.PACKET_SIZE
    for i in range(blocks_n):
            
        data = bytearray(file.read(core.PACKET_SIZE))

        if not data:
            raise "stop"

        # The last read bytes needs a right padding to be XORed in the future
        if len(data) != core.PACKET_SIZE:
            data = data + bytearray(core.PACKET_SIZE - len(data))
            assert i == blocks_n-1, "Packet #{} has a not handled size of {} bytes".format(i, len(blocks[i]))

        # Paquets are condensed in the right array type
        blocks.append(np.frombuffer(data, dtype=core.NUMPY_TYPE))

    return blocks

def blocks_write(blocks, file, filesize):
    """ Write the given blocks into a file
    """

    count = 0
    for data in recovered_blocks[:-1]:
        file_copy.write(data)
        count += len(data)

    # Convert back the bytearray to bytes and shrink back 
    last_bytes = bytes(recovered_blocks[-1])
    shrinked_data = last_bytes[:filesize % core.PACKET_SIZE]
    file_copy.write(shrinked_data)

#########################################################
    
if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Robust implementation of LT Codes encoding/decoding process.")
    parser.add_argument("filename", help="file path of the file to split in blocks")
    parser.add_argument("-r", "--redundancy", help="the wanted redundancy.", default=2.0, type=float)
    parser.add_argument("--systematic", help="ensure that the k first drops are exactaly the k first blocks (systematic LT Codes)", action="store_true")
    parser.add_argument("--verbose", help="increase output verbosity", action="store_true")
    parser.add_argument("--x86", help="avoid using np.uint64 for x86-32bits systems", action="store_true")
    args = parser.parse_args()

    core.NUMPY_TYPE = np.uint32 if args.x86 else core.NUMPY_TYPE
    core.SYSTEMATIC = True if args.systematic else core.SYSTEMATIC 
    core.VERBOSE = True if args.verbose else core.VERBOSE    

    with open(args.filename, "rb") as file:

        print("Redundancy: {}".format(args.redundancy))
        print("Systematic: {}".format(core.SYSTEMATIC))

        filesize = os.path.getsize(args.filename)
        print("Filesize: {} bytes".format(filesize))

        # Splitting the file in blocks & compute drops
        file_blocks = blocks_read(file, filesize)
        file_blocks_n = len(file_blocks)
        drops_quantity = int(file_blocks_n * args.redundancy)

        print("Blocks: {}".format(file_blocks_n))
        print("Drops: {}\n".format(drops_quantity))

        # Generating symbols (or drops) from the blocks
        file_symbols = []
        for curr_symbol in encode(file_blocks, drops_quantity=drops_quantity):
            file_symbols.append(curr_symbol)

        # HERE: Simulating the loss of packets?

        # Recovering the blocks from symbols
        recovered_blocks, recovered_n = decode(file_symbols, blocks_quantity=file_blocks_n)
        
        if core.VERBOSE:
            print(recovered_blocks)
            print("------ Blocks :  \t-----------")
            print(file_blocks)

        if recovered_n != file_blocks_n:
            print("All blocks are not recovered, we cannot proceed the file writing")
            exit()

        splitted = args.filename.split(".")
        if len(splitted) > 1:
            filename_copy = "".join(splitted[:-1]) + "-copy." + splitted[-1] 
        else:
            filename_copy = args.filename + "-copy"

        # Write down the recovered blocks in a copy 
        with open(filename_copy, "wb") as file_copy:
            blocks_write(recovered_blocks, file_copy, filesize)

        print("Wrote {} bytes in {}".format(os.path.getsize(filename_copy), filename_copy))


