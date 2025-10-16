import os
import subprocess

class BuildRule:
    def __init__(self, deps: list[str], task):
        if type(deps) is not list:
            raise TypeError(f"deps {deps} should be a list")
        self.deps = deps

        if not callable(task):
            raise TypeError(f"task {task} should be callable")
        self.task = task


class BuildSystem:
    def __init__(self):
        self.rules = {}


    def add_rule(self, target: str, rule: BuildRule) -> None:
        if type(target) is not str:
            raise TypeError(f"target {target} should be a string")
        if not isinstance(rule, BuildRule):
            raise TypeError(f"rule {rule} should be a BuildRule or inherited from it")
        self.rules[target] = rule


    def build(self, target: str):
        if type(target) is not str:
            raise TypeError(f"target {target} should be a string")

        if target not in self.rules:
            raise ValueError(f"No rule for target {target}")

        if self.circular(target):
            raise RecursionError(f"The dependency chain for {target} is circular")

        for dep in self.rules[target].deps:
            if dep in self.rules:
                self.build(dep)

        if not os.path.exists(target):
            self.rules[target].task(self.rules[target], target)
            return

        for dep in self.rules[target].deps:
            if os.path.getmtime(target) < os.path.getmtime(dep):
                self.rules[target].task(self.rules[target], target)
                return


    def circular(self, target: str, dependents: set[str]=set()) -> bool:
        if type(target) is not str:
            raise TypeError(f"target {target} should be a string")

        if type(dependents) is not set:
            raise TypeError(f"dependendts {dependents} should be a set")

        if target in dependents:
            return True

        if target not in self.rules:
            return False

        for dep in self.rules[target].deps:
            if self.circular(dep, dependents.union({target})):
                return True

        return False


    def main(self, *args) -> None:
        if len(args) < 2:
            raise TypeError("vrog.main: args should be atleast program name and target")
        self.build(args[1])


def run_cmd(cmd: str) -> subprocess.CompletedProcess:
        if type(cmd) is not str:
            raise TypeError(f"cmd {cmd} should be a string")
        return subprocess.run(["bash", "-c", cmd], check=True)


