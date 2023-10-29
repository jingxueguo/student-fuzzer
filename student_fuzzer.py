from fuzzingbook import GreyboxFuzzer as gbf
from fuzzingbook import Coverage as cv
from fuzzingbook import MutationFuzzer as mf
from fuzzingbook.Fuzzer import Runner

import traceback
import numpy as np
import time

from typing import Any, Set, Callable, Tuple

from bug import entrypoint
from bug import get_initial_corpus

## You can re-implement the coverage class to change how
## the fuzzer tracks new behavior in the SUT

class MyCoverage(cv.Coverage): # path coverage, not line coverage originally
    def __init__(self):
        super().__init__()

    # def coverage(self):
    #     """The set of executed line pairs"""
    #     coverage = set()
    #     past_line = None
    #     for line in self.trace():
    #         if past_line is not None:
    #             coverage.add((past_line, line))
    #         past_line = line
        
    #     # print(f"coverage={coverage}")

    #     return coverage
    
    def coverage(self) -> Set[cv.Location]:
        """The set of executed lines, as (function_name, line_number) pairs"""
        return set(self.trace())

    # def coverage(self):
    #     return self.branch_coverage

class MyFunctionRunner(Runner):
    def __init__(self, function: Callable) -> None:
        """Initialize.  `function` is a function to be executed"""
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


class MyMutationCoverageFuzzer(mf.MutationFuzzer):
    """Fuzz with mutated inputs based on coverage"""

    def reset(self) -> None:
        super().reset()
        self.coverages_seen: Set[frozenset] = set()
        # Now empty; we fill this with seed in the first fuzz runs
        self.population = []

    def run(self, runner: MyFunctionCoverageRunner) -> Any:
        """Run function(inp) while tracking coverage.
           If we reach new coverage,
           add inp to population and its coverage to population_coverage
        """
        result, outcome = super().run(runner)
        new_coverage = frozenset(runner.coverage())
        if outcome == MyFunctionRunner.PASS and new_coverage not in self.coverages_seen:
            # We have new coverage
            self.population.append(self.inp)
            self.coverages_seen.add(new_coverage)

        return result


if __name__ == "__main__":
    seed_inputs = get_initial_corpus()
    fast_schedule = gbf.AFLFastSchedule(5)
    line_runner = MyFunctionCoverageRunner(entrypoint)

    fast_fuzzer = gbf.CountingGreyboxFuzzer(seed_inputs, gbf.Mutator(), fast_schedule)
    fast_fuzzer.runs(line_runner, trials=9999)

    # my_mutation_fuzzer = MyMutationCoverageFuzzer(seed_inputs)
    # my_mutation_fuzzer.runs(line_runner, trials=9999)
