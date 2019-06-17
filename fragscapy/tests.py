import glob
import os
import string
import subprocess

# Template of the infos for each modification
MODIF_TEMPLATE = ("Modification n°{i}{repeat}:\n"
                  "> INPUT:\n"
                  "{input_modlist}\n"
                  "\n"
                  "> OUTPUT:\n"
                  "{output_modlist}\n"
                  "=================================================="
                  "\n"
                  "\n")


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


class TestPatterns(object):
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
        return self.cmd_pattern.format(i=i, j=j)

    def get_stdout(self, i, j):
        if self.stdout:
            if self.stdout_pattern is None:
                return None
            fname = self.stdout_pattern.format(i=i, j=j)
            if fname not in self.open_fd:
                os.makedirs(os.path.dirname(fname), exist_ok=True)
                self.open_fd[fname] = open(fname, "ab")
            return self.open_fd[fname]
        return subprocess.PIPE

    def get_stderr(self, i, j):
        if self.stderr:
            if self.stderr_pattern is None:
                return None
            fname = self.stderr_pattern.format(i=i, j=j)
            if fname not in self.open_fd:
                os.makedirs(os.path.dirname(fname), exist_ok=True)
                self.open_fd[fname] = open(fname, "ab")
            return self.open_fd[fname]
        return subprocess.PIPE

    def get_local_pcap(self, i, j):
        if self.local_pcap_pattern is None:
            return None
        fname = self.local_pcap_pattern.format(i=i, j=j)
        os.makedirs(os.path.dirname(fname), exist_ok=True)
        return fname

    def get_remote_pcap(self, i, j):
        if self.remote_pcap_pattern is None:
            return None
        fname = self.remote_pcap_pattern.format(i=i, j=j)
        os.makedirs(os.path.dirname(fname), exist_ok=True)
        return fname

    def get(self, i, j):
        return {
            "cmd": self.get_cmd(i, j),
            "stdout": self.get_stdout(i, j),
            "stderr": self.get_stderr(i, j),
            "local_pcap": self.get_local_pcap(i, j),
            "remote_pcap": self.get_remote_pcap(i, j),
        }

    def close_stdout(self, i, j):
        if self.stdout and self.stdout_pattern is not None:
            fname = self.stdout_pattern.format(i=i, j=j)
            if fname in self.open_fd:
                self.open_fd[fname].close()
                del self.open_fd[fname]

    def close_stderr(self, i, j):
        if self.stderr and self.stderr_pattern is not None:
            fname = self.stderr_pattern.format(i=i, j=j)
            if fname in self.open_fd:
                self.open_fd[fname].close()
                del self.open_fd[fname]

    def close(self, i, j):
        self.close_stderr(i, j)
        self.close_stdout(i, j)

    def close_all(self):
        for fd in self.open_fd.values():
            fd.close()

    def remove_all(self):
        if self.stdout and self.stdout_pattern is not None:
            rm_pattern(self.stdout_pattern)
        if self.stderr and self.stderr_pattern is not None:
            rm_pattern(self.stderr_pattern)
        if self.local_pcap_pattern is not None:
            rm_pattern(self.local_pcap_pattern)
        if self.remote_pcap_pattern is not None:
            rm_pattern(self.remote_pcap_pattern)


class TestCase(object):
    def __init__(self, **kwargs):
        self.cmd = kwargs.pop("cmd")
        self.stdout = kwargs.pop("stdout", False)
        self.stderr = kwargs.pop("stderr", False)
        self.local_pcap = kwargs.pop("local_pcap", None)
        self.remote_pcap = kwargs.pop("remote_pcap", None)
        self.test_id = kwargs.pop("test_id")
        self.result = None

    def run(self):
        """Launches the user command in a sub-process.

        Redirect stdout and stderr to the corresponding files.

        Args:
            i: current modlist iteration number, used for formating the
                filenames.
            j: current repeat iteration number, used for formating the
                filenames.
        """
        # Run the command
        self.result = subprocess.run(self.cmd, stdout=self.stdout,
                                     stderr=self.stderr, shell=True)

    def is_done(self):
        return self.result is not None

    def is_success(self):
        return self.is_done() and self.result.returncode == 0

    def is_failure(self):
        return self.is_done() and self.result.returncode != 0


class RepeatedTestCase(object):
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
    def __init__(self, **kwargs):
        self.ml_iterator = kwargs.pop("ml_iterator")
        self.modif_file_pattern = kwargs.pop("modif_file_pattern", None)
        self.test_patterns = TestPatterns(**kwargs)
        self.tests_generated = list()

    def flush_modif_files(self):
        """Deletes all the files that match `modif_file_pattern`."""
        if self.modif_file_pattern is not None:
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
