import sys


# convert to unicode
if sys.version_info < (3,):
    def u(x):
        # pylint: disable=E0602
        return unicode(x)
else:
    def u(x):
        return str(x)
