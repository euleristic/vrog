#!/usr/bin/python3

import sys

sys.path.append("../..")
import vrog

def main():
    bs = vrog.BuildSystem()

    bs.add_ctarget(target="example.out", sources=["a.c", "b.c", "c.c", "main.c"])

    bs.add_clean()
    
    bs.build(sys.argv[1])

if __name__ == "__main__":
    main()
