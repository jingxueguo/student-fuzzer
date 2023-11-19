from fuzzingbook import GreyboxFuzzer as gbf
from fuzzingbook import Coverage as cv
from fuzzingbook import MutationFuzzer as mf
from fuzzingbook.Fuzzer import Runner

import traceback
import numpy as np
import time

from typing import Any, Set, Callable, Tuple, Union
import pickle
import hashlib

from bug import entrypoint
from bug import get_initial_corpus

## You can re-implement the coverage class to change how
## the fuzzer tracks new behavior in the SUT

class MyCoverage(cv.Coverage): # path coverage, not line coverage originally
    def __init__(self):
        super().__init__()
    
    def coverage(self):
        """The set of executed line pairs"""
        coverage = set()
        past_line = None
        mid_line = None
        for line in self.trace():
            if past_line is None:
                past_line = line
            elif mid_line is None:
                mid_line = line
            else:
                coverage.add((past_line, mid_line, line))
                past_line = mid_line
                mid_line = line
        return coverage

class MyFunctionRunner(Runner):
    def __init__(self, function: Callable) -> None:
        super().__init__()
        self.function = function

    def run_function(self, inp: str) -> Any:
        return self.function(inp)

    def run(self, inp: str) -> Tuple[Any, str]:
        try:
            result = self.run_function(inp)
            outcome = self.PASS
        except Exception:
            result = None
            outcome = self.FAIL

        return result, outcome


class MyFunctionCoverageRunner(MyFunctionRunner):
    def __init__(self, function: Callable) -> None:
        super().__init__(function)
        self._coverage = None

    def run_function(self, inp: str) -> Any:
        with MyCoverage() as cov:
            try:
                result = super().run_function(inp)
            except Exception as exc:
                self._coverage = cov.coverage()
                raise exc

        self._coverage = cov.coverage()
        return result

    def coverage(self):
        return self._coverage
    

if __name__ == "__main__":
    seed_inputs = get_initial_corpus()
    fast_schedule = gbf.AFLFastSchedule(5)
    line_runner = MyFunctionCoverageRunner(entrypoint)
    # line_runner = mf.FunctionCoverageRunner(entrypoint)

    fast_fuzzer = gbf.CountingGreyboxFuzzer(seed_inputs, gbf.Mutator(), fast_schedule)
    n = 99999999
    start = time.time()
    fast_fuzzer.runs(line_runner, trials=n)
    end = time.time()