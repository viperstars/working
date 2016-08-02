#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time


class test(object):
    def __init__(self):
        self._time = dict()
        self.a = 1
        self.b = 2

    def __getattr__(self, name):
        return 3

    def __setattr__(self, name, value):
        if name != "_time":
            self._time["{}_settime".format(name)] = time.time()
        object.__setattr__(self, name, value)

    def __getattribute__(self, name):
        if name != "_time":
            self._time["{}_gettime".format(name)] = time.time()
        return object.__getattribute__(self, name)

if __name__ == "__main__":
    a = test()
    print a.a
    print a.b
    print a.c
    a.d = 4
    print a.d
    print a._time
