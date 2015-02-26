#! /usr/bin/env python
#! /usr/local/env python

# cannot do 'from . import boxbox' because relative imports don't work the
# way you expect when calling this file directly (e.g. python boxbox)
import boxbox
#from . import boxbox

"""
# only needed for relative imports
if not __package__ and False:
    # http://stackoverflow.com/questions/2943847/\
    #     nightmare-with-relative-imports-how-does-pep-366-work
    # The following assumes the script is in the top level of the package
    # directory.  We use dirname() to help get the parent directory to add
    # to sys.path, so that we can import the current package.  This is
    # necessary since when invoked directly, the 'current' package is not
    # automatically imported.
    parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(1, parentdir)
    import boxbox
    __package__ = str('boxbox')
    # now you can use relative imports here that will work regardless of
    # how this python file was accessed (either through 'import', through
    # 'python -m', or directly.
"""


if __name__ == '__main__':
    boxbox.boxbox.CLI()
