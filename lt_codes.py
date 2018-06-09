import os
import time
import math
import argparse
import random
from random import choices
import numpy as np
import numpy.ma as ma

SYSTEMATIC = False
VERBOSE = False
PACKET_SIZE = 65536
# PACKET_SIZE = 32768
# PACKET_SIZE = 16384
# PACKET_SIZE = 4096
# PACKET_SIZE = 1024
ROBUST_FAILURE_PROBABILITY = 0.01
NUMPY_TYPE = np.uint64
# NUMPY_TYPE = np.uint32
# NUMPY_TYPE = np.uint16
# NUMPY_TYPE = np.uint8
EPSILON = 0.00001

def blocks_read(file, filesize):
    """ Read the given file by blocks of `PACKET_SIZE` and use np.frombuffer() improvement.

    Byt default, we store each octet into a np.uint8 array space, but it is also possible
    to store up to 8 octets together in a np.uint64 array space.  
    
    This process is not saving memory but it helps reduce dimensionnality, especially for the 
    XOR operation in the encoding. Example:
    * np.frombuffer(b'\x01\x02', dtype=np.uint8) => array([1, 2], dtype=uint8)
    * np.frombuffer(b'\x01\x02', dtype=np.uint16) => array([513], dtype=uint16)
    """

    blocks_n = math.ceil(filesize / PACKET_SIZE)
    blocks = []

    # Read data by blocks of size PACKET_SIZE
    for i in range(blocks_n):
            
        data = bytearray(file.read(PACKET_SIZE))

        if not data:
            raise "stop"

        # The last read bytes needs a right padding to be XORed in the future
        if len(data) != PACKET_SIZE:
            data = data + bytearray(PACKET_SIZE - len(data))
            assert i == blocks_n-1, "Packet #{} has a not handled size of {} bytes".format(i, len(blocks[i]))

        # Paquets are condensed in the right array type
        blocks.append(np.frombuffer(data, dtype=NUMPY_TYPE))

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
    shrinked_data = last_bytes[:filesize % PACKET_SIZE]
    file_copy.write(shrinked_data)

def log(process, iteration, total, start_time):
    """Log the processing in a gentle way, each seconds"""
    global log_actual_time
    
    if "log_actual_time" not in globals():
        log_actual_time = time.time()

    if time.time() - log_actual_time > 1 or iteration == total - 1:
        log_actual_time = time.time()
        speed = (iteration + 1) / (log_actual_time - start_time + EPSILON) * PACKET_SIZE / (1024 * 1024)
        print("-- {}: {}/{} - {:.2%} symbols at {:.2f} MB/s".format(process, iteration + 1, total, (iteration + 1) / total, speed), end="\r", flush=True)

# //////////////////

class Symbol:
    def __init__(self, index, degree, data):
        self.index = index
        self.degree = degree
        self.data = data

    def log(self, blocks_quantity):
        neighbors, _ = generate_indexes(self.index, self.degree, blocks_quantity)
        print("symbol_{} degree={}\t {}".format(self.index, self.degree, neighbors))
        

def ideal_distribution(N):
    """ Create the ideal soliton distribution. 
    In practice, this distribution gives not the best results
    Cf. https://en.wikipedia.org/wiki/Soliton_distribution
    """

    probabilities = [0, 1 / N]
    probabilities += [1 / (k * (k - 1)) for k in range(2, N+1)]
    probabilities_sum = sum(probabilities)

    assert probabilities_sum >= 1 - EPSILON and probabilities_sum <= 1 + EPSILON, "The ideal distribution should be standardized"
    return probabilities

def robust_distribution(N):
    """ Create the robust soliton distribution. 
    This fixes the problems of the ideal distribution
    Cf. https://en.wikipedia.org/wiki/Soliton_distribution
    """

    # The choice of M is not a part of the distribution ; it may be improved
    # We take the median and add +1 to avoid possible division by zero 
    M = N // 2 + 1 
    R = N / M

    extra_proba = [0] + [1 / (i * M) for i in range(1, M)]
    extra_proba += [math.log(R / ROBUST_FAILURE_PROBABILITY) / M]  # Spike at M
    extra_proba += [0 for k in range(M+1, N+1)]

    probabilities = np.add(extra_proba, ideal_distribution(N))
    probabilities /= np.sum(probabilities)
    probabilities_sum = np.sum(probabilities)

    assert probabilities_sum >= 1 - EPSILON and probabilities_sum <= 1 + EPSILON, "The robust distribution should be standardized"
    return probabilities

def get_degrees_from(distribution_name, N, k):
    """ Returns the random degrees from a given distribution of probabilities.
    The degrees distribution must look like a Poisson distribution and the 
    degree of the first drop is 1 to ensure the start of decoding.
    """

    if distribution_name == "ideal":
        probabilities = ideal_distribution(N)
    elif distribution_name == "robust":
        probabilities = robust_distribution(N)
    else:
        probabilities = None
    
    population = list(range(0, N+1))
    return [1] + choices(population, probabilities, k=k-1)

def generate_indexes(symbol_index, degree, blocks_quantity):
    """Randomly get `degree` indexes, given the symbol index as a seed

    Generating with a seed allows saving only the seed (and the amount of degrees) 
    and not the whole array of indexes. That saves memory, but also bandwidth when paquets are sent.

    The random indexes need to be unique because the decoding process uses dictionnaries for performance enhancements.
    Additionnally, even if XORing one block with itself among with other is not a problem for the algorithm, 
    it is better to avoid uneffective operations like that.

    To be sure to get the same random indexes, we need to pass 
    """

    if SYSTEMATIC and symbol_index < blocks_quantity:
        indexes = [symbol_index]               
        degree = 1     
    else:
        random.seed(symbol_index)
        indexes = random.sample(range(blocks_quantity), degree)

    return indexes, degree
   
def encode(blocks, drops_quantity):
    """ Iterative encoding - Encodes new symbols and yield them.
    Encoding one symbol is described as follow:

    1.  Randomly choose a degree according to the degree distribution, save it into "deg"
        Note: below we prefer to randomly choose all the degrees at once for our symbols.

    2.  Choose uniformly at random 'deg' distinct input blocs. 
        These blocs are also called "neighbors" in graph theory.
    
    3.  Compute the output symbol as the combination of the neighbors.
        In other means, we XOR the chosen blocs to produce the symbol.
    """

    # Display statistics
    blocks_n = len(blocks)
    print("Blocks:", blocks_n)
    print("Drops:", drops_quantity)
    print("Generating graph...")

    assert blocks_n <= drops_quantity, "Because of the unicity in the random neighbors, it is need to drop at least the same amount of blocks"

    # Generate random indexes associated to random degrees, seeded with the symbol id
    random_degrees = get_degrees_from("robust", blocks_n, k=drops_quantity)

    print("Ready for encoding.", flush=True)
    start_time = time.time()

    for i in range(drops_quantity):
        
        # Get the random selection, generated precedently (for performance)
        selection_indexes, deg = generate_indexes(i, random_degrees[i], blocks_n)

        # Xor each selected array within each other gives the drop (or just take one block if there is only one selected)
        drop = blocks[selection_indexes[0]]
        for n in range(1, deg):
            drop = np.bitwise_xor(drop, blocks[selection_indexes[n]])
            # drop = drop ^ blocks[selection_indexes[n]] # according to my tests, this has the same performance

        # Create symbol, then log the process
        symbol = Symbol(index=i, degree=deg, data=drop)
        
        if VERBOSE:
            symbol.log(blocks_n)

        log("Encoding", i, drops_quantity, start_time)

        yield symbol

    print("\n----- Correctly dropped {} symbols (packet size={})".format(drops_quantity, PACKET_SIZE))

def recover_graph(symbols, blocks_quantity):
    """ Get back the same random indexes (or neighbors), thanks to the symbol id as seed.
    For an easy implementation purpose, we register the indexes as property of the Symbols objects.
    """

    for symbol in symbols:
        
        neighbors, deg = generate_indexes(symbol.index, symbol.degree, blocks_quantity)
        symbol.neighbors = {x: None for x in neighbors}
        symbol.degree = deg
        assert symbol.degree == len(symbol.neighbors)

        if VERBOSE:
            symbol.log(blocks_quantity)

    return symbols

def decode(symbols, blocks_quantity):
    """ Iterative decoding - Decodes all the passed symbols to build back the data as blocks. 
    The function returns the data at the end of the process.
    
    1. Search for an output symbol of degree one
        (a) If such an output symbol y exists move to step 2.
        (b) If no output symbols of degree one exist, iterative decoding exits and decoding fails.
    
    2. Output symbol y has degree one. Thus, denoting its only neighbour as v, the
        value of v is recovered by setting v = y.

    3. Update.

    4. If all k input symbols have been recovered, decoding is successful and iterative
        decoding ends. Otherwise, go to step 1.
    """

    symbols_n = len(symbols)
    assert symbols_n > 0, "There are no symbols to decode."

    # We keep `blocks_n` notation and create the empty list
    blocks_n = blocks_quantity
    blocks = [None] * blocks_n

    # Recover the degrees and associated neighbors using the seed (the index, cf. encoding).
    symbols = recover_graph(symbols, blocks_n)
    print("Graph built back. Ready for decoding.", flush=True)
    
    solved_blocks_count = 0
    iteration_solved_count = 0
    start_time = time.time()
    
    while iteration_solved_count > 0 or solved_blocks_count == 0:
    
        iteration_solved_count = 0

        # Search for solvable symbols
        for i, symbol in enumerate(symbols):

            # Check the current degree. If it's 1 then we can recover data
            if symbol.degree == 1: 

                iteration_solved_count += 1 
                block_index = next(iter(symbol.neighbors)) 
                symbols.pop(i)

                # This symbol is redundant: another already helped decoding the same block
                if blocks[block_index] is not None:
                    continue

                blocks[block_index] = symbol.data

                if VERBOSE:
                    print("Solved block_{} with symbol_{}".format(block_index, symbol.index))
              
                # Update the count and log the processing
                solved_blocks_count += 1
                log("Decoding", solved_blocks_count, blocks_n, start_time)

                # Reduce the degrees of other symbols that contains the solved block as neighbor             
                reduce_neighbors(block_index, blocks, symbols)

    print("\n----- Solved Blocks {:2}/{:2} --".format(solved_blocks_count, blocks_n))

    return np.asarray(blocks), solved_blocks_count

def reduce_neighbors(block_index, blocks, symbols):
    """ Loop over the remaining symbols to find for a common link between 
    each symbol and the last solved block `block`

    To avoid increasing complexity and another for loop, the neighbors are stored as dictionnary
    which enable to directly delete the entry after XORing back.
    """
    
    for other_symbol in symbols:
        if other_symbol.degree > 1 and block_index in other_symbol.neighbors:
        
            # XOR the data and remove the index from the neighbors
            other_symbol.data = np.bitwise_xor(blocks[block_index], other_symbol.data)
            del other_symbol.neighbors[block_index]
            other_symbol.degree -= 1
            
            if VERBOSE:
                print("XOR block_{} with symbol_{} :".format(block_index, other_symbol.index), list(other_symbol.neighbors.keys())) 

    
if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Robust implementation of LT Codes encoding/decoding process.")
    parser.add_argument("filename", help="file path of the file to split in blocks")
    parser.add_argument("--systematic", help="ensure that the k first drops are exactaly the k first blocks (systematic LT Codes)", action="store_true")
    parser.add_argument("--verbose", help="increase output verbosity", action="store_true")
    parser.add_argument("--x86", help="avoid using np.uint64 for x86-32bits systems", action="store_true")
    args = parser.parse_args()

    NUMPY_TYPE = np.uint32 if args.x86 else NUMPY_TYPE
    SYSTEMATIC = True if args.systematic else SYSTEMATIC 
    VERBOSE = True if args.verbose else VERBOSE    

    with open(args.filename, "rb") as file:

        filesize = os.path.getsize(args.filename)
        print("Filesize: {} bytes".format(filesize))

        # Splitting the file in blocks
        file_blocks = blocks_read(file, filesize)
        file_blocks_n = len(file_blocks)

        # Generating symbols (or drops) from the blocks
        file_symbols = []
        for curr_symbol in encode(file_blocks, drops_quantity=int(file_blocks_n * 2)):
            file_symbols.append(curr_symbol)
        
        # Simulating the loss of packets
        # exit()

        # Recovering the blocks from symbols
        recovered_blocks, recovered_n = decode(file_symbols, blocks_quantity=file_blocks_n)
        
        if args.verbose:
            print(recovered_blocks)
            print("------ Blocks :  \t-----------")
            print(file_blocks)

        if recovered_n != file_blocks_n:
            print("All blocks are not recovered, we cannot proceed the file writing")
            exit()

        splitted = args.filename.split(".")
        filename_copy = "".join(splitted[:-1]) + "-copy." + splitted[-1] 

        # Write down the recovered blocks in a copy 
        with open(filename_copy, "wb") as file_copy:
            blocks_write(recovered_blocks, file_copy, filesize)

        print("Wrote {} bytes in {}".format(os.path.getsize(filename_copy), filename_copy))


