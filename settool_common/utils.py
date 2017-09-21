import sys


# convert to unicode
if sys.version_info < (3,):
    def u(x):
        # pylint: disable=E0602
        return x.encode('utf-8')
else:
    def u(x):
        return str(x)
