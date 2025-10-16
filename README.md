# vrog
A make-like build system in Python.

## How to use
Typically, a build system will have an object of the type `vrog.BuildSystem`.
This object maintains the set of rules that that govern the build system, building targets according to that rule set and providing a default interface.
Rules are described with the type `vrog.BuildRule`.
A build rule takes a list of dependencies and runs a task with it.
To add a build rule to a build system, call the `BuildSystem.add_rule` method with a target and an associated build rule.
Targets and dependencies are expected to be file paths.
Call the `BuildSystem.build` method with a target to build that target.
The build system ensures to only run the tasks necessary to keep the target up to date with respect to its dependencies.
The `BuildSystem.main` method provides a default way of interfacing with the build system.
It expects to be called with `*sys.argv` and will try to build `sys.argv[1]`.
The `vrog.run_cmd` function will interpret a string with `bash` and run it.

## Sample
To build the sample, simply change directory to `sample` and run `PYTHONPATH=.. build.py <target>`.
The targets of the sample build system are `example.out`, `clean`, `main.o`, `a.o`, `b.o` and `c.o`.
