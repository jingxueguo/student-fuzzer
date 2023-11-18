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
        for line in self.trace():
            if past_line is not None:
                coverage.add((past_line, line))
            past_line = line
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

def getPathID(coverage: Any) -> str:
    """Returns a unique hash for the covered statements"""
    pickled = pickle.dumps(coverage)
    return hashlib.md5(pickled).hexdigest()


class Seed:
    """Represent an input with additional attributes"""

    def __init__(self, data: str) -> None:
        """Initialize from seed data"""
        self.data = data

        # These will be needed for advanced power schedules
        self.coverage = set()
        self.distance: Union[int, float] = -1
        self.energy = 0.0

    def __str__(self) -> str:
        """Returns data as string representation of the seed"""
        return self.data

    __repr__ = __str__

class MyCountingGreyboxFuzzer(gbf.CountingGreyboxFuzzer):


    def run(self, runner: MyFunctionCoverageRunner) -> Tuple[Any, str]:  # type: ignore
        """Run function(inp) while tracking coverage.
           If we reach new coverage,
           add inp to population and its coverage to population_coverage
        """
        old_coverage = frozenset(self.coverages_seen)
        result, outcome = super().run(runner)
        new_coverage = frozenset(runner.coverage())

        # seed = Seed(self.inp)
        # seed.coverage = runner.coverage()
        # self.population.append(seed)
        if new_coverage in old_coverage:
            # We have new coverage
            # print(f'new coverage {new_coverage}')
            # print(f'old coverage {old_coverage}')
            # print(self.population)
            seed = Seed(self.inp)
            seed.coverage = runner.coverage()
            self.population.append(seed)

        path_id = getPathID(runner.coverage())
        if path_id not in self.schedule.path_frequency:
            self.schedule.path_frequency[path_id] = 1
        else:
            self.schedule.path_frequency[path_id] += 1

        return (result, outcome)
    

if __name__ == "__main__":
    seed_inputs = get_initial_corpus()
    fast_schedule = gbf.AFLFastSchedule(5)
    line_runner = MyFunctionCoverageRunner(entrypoint)

    fast_fuzzer = MyCountingGreyboxFuzzer(seed_inputs, gbf.Mutator(), fast_schedule)
    fast_fuzzer.runs(line_runner, trials=999999999)


    # seed_inputs = get_initial_corpus()
    # fast_schedule = gbf.AFLFastSchedule(5)
    # line_runner = mf.FunctionCoverageRunner(entrypoint)

    # fast_fuzzer = gbf.CountingGreyboxFuzzer(seed_inputs, gbf.Mutator(), fast_schedule)
    # fast_fuzzer.runs(line_runner, trials=999999999)
    # print(fast_fuzzer.population)
