#!/usr/bin/python3

import vrog
import os
import sys

def main():
    bs = vrog.BuildSystem()

    def link(rule, target):
        cmd = f"cc -o {target} {' '.join(rule.deps)}"
        print(cmd)
        vrog.run_cmd(cmd)

    bs.add_rule("example.out", vrog.BuildRule(["a.o", "b.o", "c.o", "main.o"], link))


    def compile(rule, target):
        cmd = f"cc -c -o {target} {rule.deps[0]}"
        print(cmd)
        vrog.run_cmd(cmd)

    for trans_unit in ["a", "b", "c", "main"]:
        bs.add_rule(f"{trans_unit}.o", vrog.BuildRule([f"{trans_unit}.c", f"{trans_unit}.h"], compile))

    def clean(rule, target):
        for f in ["example.out", "a.o", "b.o", "c.o", "main.o"]:
            if os.path.exists(f):
                os.remove(f)

    bs.add_rule("clean", vrog.BuildRule([], clean))
    
    bs.main(*sys.argv)


if __name__ == "__main__":
    main()
