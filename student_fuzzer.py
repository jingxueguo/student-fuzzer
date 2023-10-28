from fuzzingbook import GreyboxFuzzer as gbf
from fuzzingbook import Coverage as cv
from fuzzingbook import MutationFuzzer as mf

import traceback
import numpy as np
import time

from typing import Any, Set

from bug import entrypoint
from bug import get_initial_corpus

## You can re-implement the coverage class to change how
## the fuzzer tracks new behavior in the SUT

class MyCoverage(cv.Coverage): # path coverage, not line coverage originally
    # def __init__(self):
    #     super.__init__()
    #     self.branch_coverage = {}

    # def track_branch_coverage(self, function_name, prev_block, cur_block):
    #     # Implement your custom coverage tracking logic here
    #     # For example, you might want to track coverage based on specific function or line conditions
    #     branch_key = (function_name, prev_block, cur_block)

    #     # Update the hash table
    #     if branch_key in self.branch_coverage:
    #         self.branch_coverage[branch_key] += 1
    #     else:
    #         self.branch_coverage[branch_key] = 1
    #     pass

    # def coverage(self):
    #     # custom_coverage = set()
    #     # for entry in self.trace():
    #     #     function_name, line_number = entry
    #     #     # Track custom coverage based on your criteria
    #     #     self.track_custom_coverage(function_name, line_number)
    #     #     custom_coverage.add(entry)
    #     return self.branch_coverage
    def coverage(self) -> Set[cv.Location]:
        """The set of executed lines, as (function_name, line_number) pairs"""
        return set(self.trace())


class MyFunctionCoverageRunner(mf.FunctionRunner):
    def run_function(self, inp: str) -> Any:
        with MyCoverage() as cov:
            try:
                result = super().run_function(inp)
            except Exception as exc:
                self._coverage = cov.coverage()
                raise exc

        self._coverage = cov.coverage()
        return result

    def coverage(self) -> Set[cv.Location]:
        return self._coverage

## You can re-implement the fuzzer class to change your
## fuzzer's overall structure

# class MyFuzzer(gbf.GreyboxFuzzer):
#
#     def reset(self):
#           <your implementation here>
#
#     def run(self, runner: gbf.FunctionCoverageRunner):
#           <your implementation here>
#   etc...

## The Mutator and Schedule classes can also be extended or
## replaced by you to create your own fuzzer!


    
# When executed, this program should run your fuzzer for a very 
# large number of iterations. The benchmarking framework will cut 
# off the run after a maximum amount of time
#
# The `get_initial_corpus` and `entrypoint` functions will be provided
# by the benchmarking framework in a file called `bug.py` for each 
# benchmarking run. The framework will track whether or not the bug was
# found by your fuzzer -- no need to keep track of crashing inputs
if __name__ == "__main__":
    seed_inputs = get_initial_corpus()
    fast_schedule = gbf.AFLFastSchedule(5)
    line_runner = MyFunctionCoverageRunner(entrypoint)

    fast_fuzzer = gbf.CountingGreyboxFuzzer(seed_inputs, gbf.Mutator(), fast_schedule)
    fast_fuzzer.runs(line_runner, trials=999999999)

# runner is the one that accesses the coverage!