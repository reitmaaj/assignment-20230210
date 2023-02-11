"""
NAME
    fibonaccier.py - redundant, concurrent Fibonacci number calculation


SYNOPSIS
    python3 fibonaccier.py [N]


DESCRIPTION
    The N argument, if provided on the command line, is a positive integer
    (as per specification) denoting the N-th Fibonacci number to calculate,
    where Fibonacci numbers are defined by the following well-known recurrence:
    
        Fibonacci(0) -> 0
        Fibonacci(1) -> 1
        Fibonacci(n) -> Fibonacci(n - 1) + Fibonacci(n - 2) otherwise.

    If N is not provided on the command line, it is read from the standard
    input.
    
    The script runs two concurrent computations of the N-th Fibonacci number,
    returning the result and information on which of the concurrent tasks
    finished first (ties, while unlikely, are broken to favor the second task).

    Additionally, the concurrent tasks are randomly delayed. Delays are
    implemented as random sleep up to one second for each recursive call in the
    Fibonacci calculation, and so for large N they may compound, yielding
    slow execution.


IMPLEMENTATION
    Below attached is the verbatim specification for the assignment.
    
        // Fibonaccier: Read positive (>0) number n (from stdin or cmdline).
        // Make 2 asynchronous/concurrent calls to a function fib(...) which
        // - a) includes a random delay of up to 1 second
        // - b) calculates and returns the fibonacci number calculated
        // using the following recursive formula:
        //    Fib(0) = 0
        //    Fib(1) = 1
        //    Fib(n) = Fib(n-1) + Fib(n-2)
        // Wait until both of the asynchronous calls finish.

        // Print out the resulting Fibonacci number Fib(n), and which one of
        // the two calls finished out first.
        //
        // If you are unsure how to go about it, consider implementing
        // the solution incrementally e.g. as follows:
        //   1. Implement a synchronous Fibonacci function without
        //      the random delay. Verify it produces the correct result.
        //   2. Change it into an async function. Verify it still works.
        //   3. Add the random delay into the function.
        //   4. Implement the 2 concurrent async calls to this function

    The main logic is contained in functions `fib` and `_fib`, where `fib` is
    a wrapper function for calling the the recursive Fibonacci calculation
    and timing the completion of the call. `_fib` is a naive recursive
    implementation of calculating Fibonacci numbers, and also contains the
    specification-mandated random delay.

    `resolve_input` and `resolve_output` functions handle input and output,
    respectively. Input is read either from command line arguments or standard
    input, depending on number of command line arguments passed. Output is
    adjusted to reflect which of the Fibonacci calculations finished first.

    Note that the specification for this assignment was interpreted to imply
    that the random delay applies to each recursive call in the Fibonacci
    calculation, not just once. (In the latter case, calling `asyncio.sleep`
    should be moved to the wrapper `fib` function.)

    Per specification, only strictly positive integers are allowed as input.

    Also, the Fibonacci implementation is not memoized (memoization would i.a.
    affect the accumulation of the total delay: execution time would
    significantly improve due to fewer delays).
    
    Some type annotations are applied.


EXAMPLES
    Running the following:
    
        python3 fibonaccier.py 6

    would yield the following output, assuming the first concurrent task
    finished first:

        fib(6) -> 8 (first task finished first)
 

TESTING
    To smoke test, run
    
        python3 -m doctest fibonaccier.py

    No output implies all tests pass. Note that the tests will take a while
    due to compounding specification-imposed random delays (each up to a second)
    in computing the Fibonacci numbers.

    >>> from sys import version_info
    >>> assert version_info >= (3, 7, 0)


AUTHOR
    Jukka Reitmaa

"""

from sys import argv
from sys import stdout
from sys import stderr
from asyncio import run
from asyncio import sleep
from asyncio import gather
from random import random
from time import time_ns
from typing import List
from typing import Tuple

# helpers

class UsageError(Exception):
    """
    Script-specific usage errors.
    """
    pass


# main implementation

async def _fib(n: int) -> int:
    """
    A recursive implementation of Fibonacci numbers (on large n, may exhaust
    call stack and will be slow to complete due to compounding random delays).
    
    :param n:   the ordinal of the Fibonacci number to calculate
    :return:    the n-th Fibonacci number
    
    >>> from asyncio import run
    >>> run(_fib(0))
    0
    >>> run(_fib(1))
    1
    >>> run(_fib(2))
    1
    >>> run(_fib(6))
    8
    """

    await sleep(random()) # `random()` returns a PRN between 0.0 and 1.0
    if n == 0:
        return 0
    if n == 1:
        return 1
    return await _fib(n - 1) + await _fib(n - 2)


async def fib(n: int) -> Tuple[int, int]:
    """
    A wrapper for the actual Fibonacci calculation (`_fib`). Returns the
    result and a high-precision timestamp of finishing time.

    :param n:   the ordinal of the Fibonacci number to calculate
    :return:    tuple n-th Fibonacci number, high-res timestamp of completion

    >>> from asyncio import run
    >>> nth_fib, timestamp = run(fib(6))
    >>> assert nth_fib == 8
    >>> assert type(timestamp) == int
    """

    nth_fib = await _fib(n)
    timestamp = time_ns()
    return nth_fib, timestamp


def resolve_input(*args) -> int:
    """
    Obtain the input parameter to the Fibonacci calculations.
    
    If no command line arguments were provided, read from standard input using
    `input` builtin.
    
    If a command line argument was provided, parse it as an integer.

    >>> resolve_input('3')
    3
    """
    
    if len(args) == 0: # no command line input -> read stdin
        n = int(input())
    elif len(args) == 1: # else parse command line input as an integer
        n = int(args[0])

    # if valid input, pass it on...
    if n > 0:
        return n

    # ... else complain
    raise UsageError(f'bad command line arguments: {" ".join(args)}')


def resolve_output(n: int, results: List[Tuple[int, int]]) -> str:
    """
    Obtain output for the command.
    
    Returns a string describing the user input, the corresponding Fibonacci
    number and indication of which of the two concurrent tasks finished first. 
    """
    
    # destructure results
    nth_fib0, timestamp0 = results[0]
    nth_fib1, timestamp1 = results[1]

    # sanity check Fibonacci results
    if nth_fib0 != nth_fib1:
        raise RuntimeError(f'bad results: {nth_fib0} is not {nth_fib1}')

    # resolve which run finished first
    # break tie in favor of the second run
    if timestamp0 < timestamp1:
        return f'fib({n}) -> {nth_fib0} (first task finished first)'
    else:
        return f'fib({n}) -> {nth_fib0} (second task finished first)'


# script entry

async def main(_, *args):
    try:
    
        # resolve user input
        n = resolve_input(*args)

        # execute the concurrent Fibonacci calculations
        results = await gather(fib(n), fib(n))

        # resolve and print script result to stdout
        print(resolve_output(n, results), file=stdout)

    except UsageError as exc:
        print(__doc__, file=stderr)
    except BaseException as exc:
        raise exc


if __name__ == '__main__':
    run(main(*argv))


