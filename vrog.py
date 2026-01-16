import os
import subprocess
import dataclasses

class BuildRule:
    def __init__(self, deps: list[str], task):
        if type(deps) is not list:
            raise TypeError(f"deps {deps} should be a list")
        self.deps = deps

        if not callable(task):
            raise TypeError(f"task {task} should be callable")
        self.task_impl = task


    def task(self, target):
        self.task_impl(self, target)


@dataclasses.dataclass
class Compiler():
    compiler: str="cc"
    standard: str=None
    optimization: int=None
    warnings: list[str]=dataclasses.field(default_factory=list)
    definitions: list[str]=dataclasses.field(default_factory=list)
    extra_args: list[str]=dataclasses.field(default_factory=list)


class CompilerRule(BuildRule):
    def __init__(
        self,
        source: str,
        compiler: Compiler=Compiler()
    ):
        if type(source) is not str:
            raise TypeError(f"source {source} should be a string")
        if type(compiler) is not Compiler:
            raise TypeError(f"compiler {compiler} should be a compiler")
        self.deps = [source]
        self.compiler = compiler


    def task(self, target):
        if type(target) is not str:
            raise TypeError(f"target {target} should be a string")
        cmd = [self.compiler.compiler, "-c"]
        if self.compiler.standard: cmd.append(f"-std={self.compiler.standard}")
        if self.compiler.optimization: cmd.append(f"-o{self.compiler.optimization}")
        cmd += ["-W" + warning for warning in self.compiler.warnings]
        cmd += self.compiler.extra_args
        cmd += self.deps
        cmd += ["-o", target]
        subprocess.run(cmd)


@dataclasses.dataclass
class Linker():
    linker: str="cc"
    libraries: list[str]=dataclasses.field(default_factory=list)
    linker_args: list[str]=dataclasses.field(default_factory=list)
    extra_args: list[str]=dataclasses.field(default_factory=list)


class LinkerRule(BuildRule):
    def __init__(
        self,
        objects: list[str],
        linker: Linker=Linker()
    ):
        if type(objects) is not list:
            raise TypeError(f"objects {objects} should be a list")
        if type(linker) is not Linker:
            raise TypeError(f"linker {linker} should be a linker")
        self.deps = objects
        self.linker = linker


    def task(self, target):
        if type(target) is not str:
            raise TypeError(f"target {target} should be a string")
        cmd = [self.linker.linker]
        cmd += ["-l" + lib for lib in self.linker.libraries]
        cmd += ["-Wl," + lib for lib in self.linker.linker_args]
        cmd += self.linker.extra_args
        cmd += self.deps
        cmd += ["-o", target]
        subprocess.run(cmd)


class CleanRule(BuildRule):
    def __init__(self, targets):
        self.deps = []
        if type(targets) is not list:
            raise TypeError(f"targets {targets} should be a list")
        self.targets = targets


    def task(self, target):
        for file in self.targets:
            if os.path.exists(file):
                print(f"rm {file}")
                os.remove(file)


class BuildSystem:
    def __init__(self):
        self.rules = {}


    def add_rule(self, target: str, rule: BuildRule) -> None:
        if type(target) is not str:
            raise TypeError(f"target {target} should be a string")
        if not isinstance(rule, BuildRule):
            raise TypeError(f"rule {rule} should be a BuildRule or inherited from it")
        self.rules[target] = rule


    def add_ctarget(
        self,
        target: str,
        sources: list[str],
        compiler: Compiler=Compiler(),
        linker: Linker=Linker()
    ):
        objects = [f"{source}.o" for source in sources]
        self.add_rule(target, LinkerRule(objects, linker))
        for obj, source in zip(objects, sources):
            self.add_rule(obj, CompilerRule(source, compiler))


    def add_clean(self):
        self.add_rule("clean", CleanRule(list(self.rules.keys())))
        

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
            print(target)
            self.rules[target].task(target)
            return

        for dep in self.rules[target].deps:
            if os.path.getmtime(target) < os.path.getmtime(dep):
                print(target)
                self.rules[target].task(target)
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


def run_cmd(cmd: str) -> subprocess.CompletedProcess:
        if type(cmd) is not str:
            raise TypeError(f"cmd {cmd} should be a string")
        return subprocess.run(["sh", "-c", cmd], check=True)


