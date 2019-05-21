"""
Some utility fonctions and objects that are used all over the code.
"""

import os
import sys

def check_perm(root=False):
    """
    Decorator to make some checks on the user's permissions.
    It exits the program if unsufficient permissions are detected.

    :param root: if set to True, ensure that user's uid is 0 before starting the function.
    """
    def _decorator(func):
        def _wrapper(*args, **kwargs):
            try:
                if root and os.geteuid() != 0:
                    raise PermissionError()
                return func(*args, **kwargs)
            except PermissionError:
                print("Permission Denied : can't execute {}".format(func.__name__))
                sys.exit(1)
        return _wrapper
    return _decorator
