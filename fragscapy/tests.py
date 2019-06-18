"""A collection of structures to represent the tests that can be run (and
tested).

The `TestSuite` object defines a modification to use (for both INPUT
and OUTPUT chains) and yields a `RepeatedTestCase` object. This object defines
the exact command and filenames to use in the test and yields a `TestCase`
object. This final object contains all the information about a single and can
run the required command.

Schema of the hierarchy of test objects::

    TestSuite
      +---> RepeatedTestCase with modification n°1
      |       +---> TestCase with modification n°1 and repetition n°1
      |       +---> TestCase with modification n°1 and repetition n°2
      |       +---> TestCase with modification n°1 and repetition n°3
      |       +---> ...
      +---> RepeatedTestCase with modification n°2
      |       +---> TestCase with modification n°2 and repetition n°1
      |       +---> ...
      +---> RepeatedTestCase with modification n°3
      |       +---> TestCase with modification n°4 and repetition n°1
      |       +---> ...
      +---> ...
"""


import glob
import os
import string
import subprocess


def rm_pattern(pattern):
    """Deletes all the files that match a formatting pattern."""
    # Build the args and kwargs to use '*' in the pattern
    args = list()
    kwargs = dict()
    for _, name, _, _ in string.Formatter().parse(pattern):
        if name is None:
            continue
        if name:
            kwargs[name] = '*'
        else:
            args.append('*')

    # Remove the corresponding files
    for f in glob.glob(pattern.format(*args, **kwargs)):
        os.remove(f)


# pylint: disable=too-many-instance-attributes
class TestPatterns(object):
    """Regroups all the patterns that creates the command and filenames at
    each test iteration.

    Any pattern uses `{i}` and `{j}` as placeholders for respectively the
    number of the current modification and the number of the current iteration
    of this modification.

    Args:
        cmd_pattern: The pattern for the command to execute.
        stdout: 'True' if the standard output of the test should be captured.
            Default is 'False'.
        stdout_pattern: The pattern of the filename to redirect the standard
            output of the test to. Use 'None' to redirect to stdout. Default
            is 'None'
        stderr: 'True' if the standard error of the test should be captured.
            Default is 'False'.
        stderr_pattern: The pattern of the filename to redirect the standard
            error of the test to. Use 'None' to redirect to stdout. Default is
            'None'.
        local_pattern: The pattern of the name of the pcap file to which the
            local packets details should be dumped to. Use 'None' to not dump
            the packet details. Default is 'None'.
        remote_pattern: The pattern of the name of the pcap file to which the
            remote packets details should be dumped to. Use 'None' to not dump
            the packet details. Default is 'None'.

    Attributes:
        cmd_pattern: The pattern for the command to execute.
        stdout: 'True' if the standard output of the test should be captured
        stdout_pattern: The pattern of the filename to redirect the standard
            output of the test to. Use 'None' to redirect to stdout.
        stderr: 'True' if the standard error of the test should be captured
        stderr_pattern: The pattern of the filename to redirect the standard
            error of the test to. Use 'None' to redirect to stdout.
        local_pattern: The pattern of the name of the pcap file to which the
            local packets details should be dumped to. Use 'None' to not dump
            the packet details.
        remote_pattern: The pattern of the name of the pcap file to which the
            remote packets details should be dumped to. Use 'None' to not dump
            the packet details.
        open_fd: A dictionnary that link a filename and its filedescriptor if
            it is already openned (avoid openning the same file multiple
            times).
    """
    def __init__(self, **kwargs):
        self.cmd_pattern = kwargs.pop("cmd_pattern")
        self.stdout = kwargs.pop("stdout", False)
        self.stdout_pattern = kwargs.pop("stdout_pattern", None)
        self.stderr = kwargs.pop("stderr", False)
        self.stderr_pattern = kwargs.pop("stderr_pattern", None)
        self.local_pcap_pattern = kwargs.pop("local_pcap_pattern", None)
        self.remote_pcap_pattern = kwargs.pop("remote_pcap_pattern", None)

        self.open_fd = dict()

    def get_cmd(self, i, j):
        """Returns the command based on its pattern and the given `i` and
        `j`."""
        return self.cmd_pattern.format(i=i, j=j)

    def get_stdout(self, i, j):
        """Returns the stdout file descriptor based on its pattern and the
        given `i` and `j`."""
        if self.stdout:
            if self.stdout_pattern is None:
                return None
            fname = self.stdout_pattern.format(i=i, j=j)
            if fname not in self.open_fd:
                if os.path.dirname(fname):
                    os.makedirs(os.path.dirname(fname), exist_ok=True)
                self.open_fd[fname] = open(fname, "ab")
            return self.open_fd[fname]
        return subprocess.PIPE

    def get_stderr(self, i, j):
        """Returns the stderr file descriptor based on its pattern and the
        given `i` and `j`."""
        if self.stderr:
            if self.stderr_pattern is None:
                return None
            fname = self.stderr_pattern.format(i=i, j=j)
            if fname not in self.open_fd:
                if os.path.dirname(fname):
                    os.makedirs(os.path.dirname(fname), exist_ok=True)
                self.open_fd[fname] = open(fname, "ab")
            return self.open_fd[fname]
        return subprocess.PIPE

    def get_local_pcap(self, i, j):
        """Returns the local pcap filename based on its pattern and the given
        `i` and `j`."""
        if self.local_pcap_pattern is None:
            return None
        fname = self.local_pcap_pattern.format(i=i, j=j)
        if os.path.dirname(fname):
            os.makedirs(os.path.dirname(fname), exist_ok=True)
        return fname

    def get_remote_pcap(self, i, j):
        """Returns the remote pcap filename based on its pattern and the given
        `i` and `j`."""
        if self.remote_pcap_pattern is None:
            return None
        fname = self.remote_pcap_pattern.format(i=i, j=j)
        if os.path.dirname(fname):
            os.makedirs(os.path.dirname(fname), exist_ok=True)
        return fname

    def get(self, i, j):
        """Returns a dictionnary of all the generated objects based on their
        patterns and the given `i` and `j`. It can be used directly as an
        input for `TestCase`."""
        return {
            "cmd": self.get_cmd(i, j),
            "stdout": self.get_stdout(i, j),
            "stderr": self.get_stderr(i, j),
            "local_pcap": self.get_local_pcap(i, j),
            "remote_pcap": self.get_remote_pcap(i, j),
        }

    def close_stdout(self, i, j):
        """Closes the stdout file descriptor based on its pattern and the
        given `i` and `j`."""
        if self.stdout and self.stdout_pattern is not None:
            fname = self.stdout_pattern.format(i=i, j=j)
            if fname in self.open_fd:
                self.open_fd[fname].close()
                del self.open_fd[fname]

    def close_stderr(self, i, j):
        """Closes the stderr file descriptor based on its pattern and the
        given `i` and `j`."""
        if self.stderr and self.stderr_pattern is not None:
            fname = self.stderr_pattern.format(i=i, j=j)
            if fname in self.open_fd:
                self.open_fd[fname].close()
                del self.open_fd[fname]

    def close(self, i, j):
        """Closes all file descriptor based on its pattern and the
        given `i` and `j`."""
        self.close_stderr(i, j)
        self.close_stdout(i, j)

    def close_all(self):
        """Closes all open file descriptors."""
        for fname in self.open_fd:
            self.open_fd[fname].close()
            del self.open_fd[fname]

    def remove_all(self):
        """Removes all files that can match the patterns of `stdout_pattern`,
        `stderr_pattern`, `local_pcap_pattern` and `remote_pcap_pattern`."""
        if self.stdout and self.stdout_pattern is not None:
            rm_pattern(self.stdout_pattern)
        if self.stderr and self.stderr_pattern is not None:
            rm_pattern(self.stderr_pattern)
        if self.local_pcap_pattern is not None:
            rm_pattern(self.local_pcap_pattern)
        if self.remote_pcap_pattern is not None:
            rm_pattern(self.remote_pcap_pattern)


class TestCase(object):
    """A situation to be tested. It contains all the informations (filenames,
    id, command and result) that represents the test.

    Args:
        cmd: The command to run.
        stdout: The file descriptor to redirect standard output to. 'None' is
            for stdout. Default is 'None'.
        stderr: The file descriptor to redirect standard error to. 'None' is
            for stderr. Default is 'None'.
        local_pcap: The filename of the pcap file to dump local packets
            details to. 'None' is for not dumping the packet details. Default
            is 'None'
        remote_pcap: The filename of the pcap file to dump remote packets
            details to. 'None' is for not dumping the packet details. Default
            is 'None'.
        test_id: The number of this test a.k.a. `j`.

    Attributes:
        cmd: The command to run.
        stdout: The file descriptor to redirect standard output to. 'None' is
            for stdout.
        stderr: The file descriptor to redirect standard error to. 'None' is
            for stderr.
        local_pcap: The filename of the pcap file to dump local packets
            details to. 'None' is for not dumping the packet details.
        remote_pcap: The filename of the pcap file to dump remote packets
            details to. 'None' is for not dumping the packet details.
        test_id: The number of this test a.k.a. `j`.
        result: The `ProcessCompleted` returned by the subprocess or 'None' if
            not run yet.
    """

    def __init__(self, **kwargs):
        self.cmd = kwargs.pop("cmd")
        self.stdout = kwargs.pop("stdout", None)
        self.stderr = kwargs.pop("stderr", None)
        self.local_pcap = kwargs.pop("local_pcap", None)
        self.remote_pcap = kwargs.pop("remote_pcap", None)
        self.test_id = kwargs.pop("test_id")
        self.result = None

    def run(self):
        """Executes the user command in a sub-process. Redirect stdout and
        stderr to the corresponding files."""
        self.result = subprocess.run(self.cmd, stdout=self.stdout,
                                     stderr=self.stderr, shell=True)

    def is_done(self):
        """Returns 'True' if the command has been run at least once."""
        return self.result is not None

    def is_success(self):
        """Returns 'True' if the command returned a zero exitcode."""
        return self.is_done() and self.result.returncode == 0

    def is_failure(self):
        """Returns 'True' if the command returned a non-zero exitcode."""
        return self.is_done() and self.result.returncode != 0


# pylint: disable=too-few-public-methods
class RepeatedTestCase(object):
    """A series of `TestCase` that might be repeated mulitple times if
    the modifications are not deterministic.

    All the repeated tests will be run with the same modifications.

    Args:
        modlists: A 2-tuple of `(input_modlist, output_modlist)`.
        modif_file: The name of the modification file (the same for all
            repeated tests because it does not change)
        test_id: The number of this test a.k.a. 'i'.
        test_pattern: The `TestPattern` object to use for each of the tests.

    Attributes:
        input_modlist: The modification list applied on INPUT chain.
        output_modlist: The modification list applied on OUTPUT chain.
        modif_file: The name of the modification file (the same for all
            repeated tests because it does not change)
        test_id: The number of this test a.k.a. 'i'.
        test_pattern: The `TestPattern` object to use for each of the tests.
        repeat: The number of times a test case must be repeated.
        test_generated: A list of all `TestCase` objects generated so far.
    """
    def __init__(self, modlists, modif_file, test_id, test_patterns):
        self.input_modlist = modlists[0]
        self.output_modlist = modlists[1]
        self.modif_file = modif_file
        self.test_id = test_id
        self.test_patterns = test_patterns

        if (self.input_modlist.is_deterministic()
                and self.output_modlist.is_deterministic()):
            self.repeat = 1
        else:
            self.repeat = 100

        self.tests_generated = list()

    def __iter__(self):
        for j in range(self.repeat):
            test = TestCase(
                **self.test_patterns.get(self.test_id, j),
                test_id=j,
            )
            self.tests_generated.append(test)
            yield test
            # The files must be closed right after being used
            # to avoid keeping too many file descriptors opened
            self.test_patterns.close(self.test_id, j)


class TestSuite(object):
    """A series of tests to run described by some patterns and the
    `ModListGenerator`.

    Args:
        ml_iterator: An iterator over all possible 2-tuples of
            `(input_modlist, output_modlist)` that needs to be tested.
        modif_file_pattern: The pattern for the modification file (separated
            from the others because it does not require the `j` argument).
        **kwargs: All other arguments are passed to the constructor of
            `TestPatterns`.

    Attributes:
        ml_iterator: An iterator over all possible 2-tuples of
            `(input_modlist, output_modlist)` that needs to be tested.
        modif_file_pattern: The pattern for the modification file (separated
            from the others because it does not require the `j` argument).
        test_patterns: The `TestPatterns` object that will be used to generate
            the filenames and commands of each test case.
        test_generated: A list of all `RepeatedTestCase` objects generated so
            far.
    """
    def __init__(self, **kwargs):
        self.ml_iterator = kwargs.pop("ml_iterator")
        self.modif_file_pattern = kwargs.pop("modif_file_pattern")
        self.test_patterns = TestPatterns(**kwargs)
        self.tests_generated = list()

    def flush_modif_files(self):
        """Deletes all the files that match `modif_file_pattern`."""
        rm_pattern(self.modif_file_pattern)

    def flush_all_files(self):
        """Deletes all the files that could be generated during the process of
        the tests."""
        self.flush_modif_files()
        self.test_patterns.remove_all()

    def __iter__(self):
        for test_id, modlists in enumerate(self.ml_iterator):
            # Makes sure the modif_file directory exists
            modif_file = self.modif_file_pattern.format(i=test_id)
            if os.path.dirname(modif_file):
                os.makedirs(os.path.dirname(modif_file), exist_ok=True)

            # Creates a RepeatedTestCase with these modlists
            repeated_test_case = RepeatedTestCase(
                modlists,
                modif_file,
                test_id,
                self.test_patterns,
            )
            self.tests_generated.append(repeated_test_case)
            yield repeated_test_case

        # Closing all remaining files for safety
        self.test_patterns.close_all()
