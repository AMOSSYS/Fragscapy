"""
Some utility fonctions and objects that are used all over the code.
"""
import os

def check_root(func):
    """
    Decorator to check that the user is root. A PermissionError is raised
    if it is not the case.
    """
    def _decorator(*args, **kwargs):
        if os.geteuid() != 0:
            raise PermissionError("You should be root")
        return func(*args, **kwargs)
    return _decorator
