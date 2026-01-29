import os
import subprocess
import dataclasses

class BuildRule:
    """A BuildRule builds a target from its dependencies."""
    def __init__(self, deps: list[str], task):
        """Initializes a BuildRule.

        deps
          The list of dependencies to build the target.
        task
          The function which builds the target from the dependencies.
          This function should have arguments (self: BuildRule, target: str)
        """
        if type(deps) is not list:
            raise TypeError(f"deps {deps} should be a list")
        self.deps = deps

        if not callable(task):
            raise TypeError(f"task {task} should be callable")
        self.task_impl = task


    def task(self, target: str) -> None:
        """Calls the task to build target."""
        self.task_impl(self, target)


@dataclasses.dataclass
class Compiler():
    """Abstracts a compiler invocation.

    compiler
      The program to execute.
    standard
      Argument passed with self.standard_option, if not None.
    optimization
      Argument passed with self.standard_option, if not None.
    warnings
      Arguments passed with self.warning_option.
    definitions
      Arguments passed with self.definition_option.
    extra_args
      Arguments passed as they are.
    """
    compiler: str="cc"
    standard: str=None
    standard_option: str="-std="
    optimization: str=None
    optimization_option: str="-O"
    warnings: list[str]=dataclasses.field(default_factory=list)
    warning_option: str="-W"
    definitions: list[str]=dataclasses.field(default_factory=list)
    definition_option: str="-D"
    extra_args: list[str]=dataclasses.field(default_factory=list)


class CompilerRule(BuildRule):
    """A rule which compiles an object file from a source file."""
    def __init__(
        self,
        source: str,
        compiler: Compiler=Compiler()
    ):
        """Initializes a CompilerRule.

        source
          The source file to compile.
        compiler
          The compiler to invoke.
        """
        if type(source) is not str:
            raise TypeError(f"source {source} should be a string")
        if type(compiler) is not Compiler:
            raise TypeError(f"compiler {compiler} should be a compiler")
        self.source = source
        self.deps = gen_deps(source, compiler)
        self.compiler = compiler


    def task(self, target: str) -> None:
        """Invokes the compiler to build target"""
        if type(target) is not str:
            raise TypeError(f"target {target} should be a string")
        cmd = [self.compiler.compiler, "-c"]
        if self.compiler.standard:
            cmd.append(self.compiler.standard_option + self.compiler.standard)
        if self.compiler.optimization:
            cmd.append(self.optimization_option + self.compiler.optimization)
        cmd += [warning_option + warning for warning in self.compiler.warnings]
        cmd += [definition_option + definition for definition in self.compiler.definitions]
        cmd += self.compiler.extra_args
        cmd += ["-o", target]
        cmd.append(self.source)
        subprocess.run(cmd)


@dataclasses.dataclass
class Linker():
    """Abstracts a linker invocation.

    compiler
      The program to execute.
    libraries
      Arguments passed with self.library_option.
    linker_args
      Arguments passed with self.linker_arg_option.
    extra_args
      Arguments passed as they are.
    """
    linker: str="cc"
    libraries: list[str]=dataclasses.field(default_factory=list)
    library_option: str="-l"
    linker_args: list[str]=dataclasses.field(default_factory=list)
    linker_arg_option: str="-Wl,"
    extra_args: list[str]=dataclasses.field(default_factory=list)


class LinkerRule(BuildRule):
    """A rule which links a target from object files."""
    def __init__(
        self,
        objects: list[str],
        linker: Linker=Linker()
    ):
        """Initializes a LinkerRule.

        objects
          The object file to link.
        linker
          The linker to invoke.
        """
        if type(objects) is not list:
            raise TypeError(f"objects {objects} should be a list")
        if type(linker) is not Linker:
            raise TypeError(f"linker {linker} should be a linker")
        self.deps = objects
        self.linker = linker


    def task(self, target: str) -> None:
        """Invokes the linker to build target."""
        if type(target) is not str:
            raise TypeError(f"target {target} should be a string")
        cmd = [self.linker.linker]
        cmd += [self.linker.library_option + lib for lib in self.linker.libraries]
        cmd += [self.linker.linker_arg_option + link for link in self.linker.linker_args]
        cmd += self.linker.extra_args
        cmd += self.deps
        cmd += ["-o", target]
        subprocess.run(cmd)


class CleanRule(BuildRule):
    """A rule for cleaning targets."""
    def __init__(self, targets: list[str]):
        """Initializes a CleanRule.

        targets
          Targets to remove on clean.
        """
        self.deps = []
        if type(targets) is not list:
            raise TypeError(f"targets {targets} should be a list")
        self.targets = targets


    def task(self, target):
        """Removes self.targets. target argument is ignored."""
        for file in self.targets:
            if os.path.exists(file):
                print(f"rm {file}")
                os.remove(file)


def gen_deps(
    source: str,
    compiler: Compiler=Compiler(),
) -> list[str]:
    """Generates the list of dependencies of an object file"

    source
      The source of the object file.
    compiler
      The compiler that generates the dependency list.
    """
    cmd = [compiler.compiler, "-MM", "-MP"]
    cmd += [definition_option + definition for definition in compiler.definitions]
    cmd += compiler.extra_args
    cmd.append(source)
    make_rules = subprocess.run(cmd, capture_output=True, text=True).stdout
    return make_rules.replace("\\\n", "").splitlines()[0].split()[1:]


class BuildSystem:
    """A system of rules for how to build targets."""
    def __init__(self):
        """Initializes a BuildSystem."""
        self.rules = {}


    def add_rule(self, target: str, rule: BuildRule) -> None:
        """Adds a rule to the BuildSystem.

        target
          The target of the rule.
        rule
          The BuildRule providing the target's dependencies and the task which builds it.
        """
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
    ) -> None:
        """Adds a LinkerRule and CompilerRules to build a target from source files.

        target
          The target of the LinkerRule.
        sources
          The source files which build target.
        compiler
          The Compiler of the CompilerRules.
        linker
          The Linker of the LinkerRules.
        """
        objects = [f"{source}.o" for source in sources]
        self.add_rule(target, LinkerRule(objects, linker))
        for obj, source in zip(objects, sources):
            self.add_rule(obj, CompilerRule(source, compiler))


    def add_clean(self, target: str="clean") -> None:
        """Adds a CleanRules which cleans all targets in the BuildSystem.

        target
          The target to "build" which will invoke the rule.
        """
        self.add_rule(target, CleanRule(list(self.rules.keys())))
        

    def build(self, target: str) -> None:
        """Builds target, building dependencies as necessary to keep target up to date"""
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


    def circular(self, target: str, _dependents: set[str]=set()) -> bool:
        """Checks if there is a dependency circularity for target"""
        if type(target) is not str:
            raise TypeError(f"target {target} should be a string")

        if type(_dependents) is not set:
            raise TypeError(f"_dependendts {_dependents} should be a set")

        if target in _dependents:
            return True

        if target not in self.rules:
            return False

        for dep in self.rules[target].deps:
            if self.circular(dep, _dependents.union({target})):
                return True

        return False


def run_cmd(cmd: str) -> subprocess.CompletedProcess:
    """Runs cmd through the shell"""
    if type(cmd) is not str:
        raise TypeError(f"cmd {cmd} should be a string")
    return subprocess.run(["sh", "-c", cmd], check=True)


