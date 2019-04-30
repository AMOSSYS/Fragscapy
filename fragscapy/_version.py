"""Fetches the version of Fragscapy from the commit hash.

Defines the contant `__version__` based on a version number and the current
commit hash (if it can be found).
This script was mostly "inspired" from `tdqm`'s own script to determine the
version.
"""

import os
import io


__all__ = ["__version__"]

# major, minor, -extra
VERSION_INFO = 1, 0


def get_version():
    """Computes the version based on the version info and the git hash."""
    version = '.'.join(map(str, VERSION_INFO))

    # auto -extra based on commit hash (if not tagged as release)
    scriptdir = os.path.dirname(__file__)
    gitdir = os.path.abspath(os.path.join(scriptdir, "..", ".git"))
    if os.path.isdir(gitdir):
        extra = None
        # Open config file to check if we are in tqdm project
        with io.open(os.path.join(gitdir, "config"), 'r') as fh_config:
            if 'fragscapy' in fh_config.read():
                # Open the HEAD file
                with io.open(os.path.join(gitdir, "HEAD"), 'r') as fh_head:
                    extra = fh_head.readline().strip()
                # in a branch => HEAD points to file containing last commit
                if 'ref:' in extra:
                    # reference file path
                    ref_file = extra[5:]
                    branch_name = ref_file.rsplit('/', 1)[-1]

                    ref_file_path = os.path.abspath(os.path.join(
                        gitdir, ref_file
                    ))
                    # check that we are in git folder
                    # (by stripping the git folder from the ref file path)
                    if os.path.relpath(
                            ref_file_path, gitdir
                        ).replace('\\', '/') != ref_file:
                        # out of git folder
                        extra = None
                    else:
                        # open the ref file
                        with io.open(ref_file_path, 'r') as fh_branch:
                            commit_hash = fh_branch.readline().strip()
                            extra = commit_hash[:8]
                            if branch_name != "master":
                                extra += '.' + branch_name

                # detached HEAD mode, already have commit hash
                else:
                    extra = extra[:8]

        # Append commit hash (and branch) to version string if not tagged
        if extra is not None:
            try:
                with io.open(os.path.join(gitdir, "refs", "tags",
                                          'v' + version)) as fdv:
                    if fdv.readline().strip()[:8] != extra[:8]:
                        version += '-' + extra
            except FileNotFoundError:
                version += '-' + extra

    return version


# Nice string for the version
__version__ = get_version()
