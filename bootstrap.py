#!/usr/local/env python
"""
This is a bootstrap runner for executing or testing the boxbox command line
interface without installing the package.
"""
import boxbox


if __name__ == '__main__':
    boxbox.interface.CLI()
