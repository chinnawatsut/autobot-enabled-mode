#!/usr/bin/env python

from lib.autobot import Autobot
import sys

if __name__ == "__main__":
    if len(sys.argv) > 1:
        view_name = sys.argv[1]
        a = Autobot()
        a.run(view_name)
