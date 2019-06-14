import os
import subprocess

class StdFilePattern(object):
    def __init__(self, use=False, pattern=None):
        self.use = use
        self.pattern = pattern
        self.open_fd = dict()

    def get(self, i, j):
        if self.use:
            if self.pattern is not None:
                filename = self.pattern.format(i=i, j=j)
                if filename in self.open_fd:
                    return self.open_fd[filename]
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                self.open_fd[filename] = open(filename, "ab")
                return self.open_fd[filename]
            else:
                return None
        else:
            return subprocess.PIPE

    def close(self, i, j):
        if self.use and self.pattern is not None:
            filename = self.pattern.format(i=i, j=j)
            if filename not in self.open_fd:
                return False
            self.open_fd[filename].close()
            del self.open_fd[filename]
            return True
        return False

    def close_all(self):
        for fd in self.open_fd.values():
            fd.close()


class PcapFilePattern(object):
    def __init__(self, pattern=None):
        self.pattern = pattern

    def get(self, i, j):
        if self.pattern is not None:
            return self.pattern.format(i=i, j=j)
        else:
            return None


class TestCase(object):
    def __init__(self, **kwargs):
        self.in_ml = kwargs.pop("in_ml")
        self.out_ml = kwargs.pop("out_ml")
        self.cmd = kwargs.pop("cmd")
        self.stdout = kwargs.pop("stdout", False)
        self.stderr = kwargs.pop("stderr", False)
        self.local_pcap = kwargs.pop("local_pcap", None)
        self.remote_pcap = kwargs.pop("remote_pcap", None)
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


class TestSuite(object):
    def __init__(self, **kwargs):
        self.ml_iterator = kwargs.pop("ml_iterator")
        self.cmd_pattern = kwargs.pop("cmd_pattern")
        self.stdout_pattern = StdFilePattern(
            kwargs.pop("stdout", False),
            kwargs.pop("stdout_pattern", None)
        )
        self.stderr_pattern = StdFilePattern(
            kwargs.pop("stderr", False),
            kwargs.pop("stderr_pattern", None)
        )
        self.local_pcap_pattern = PcapFilePattern(
            kwargs.pop("local_pcap_pattern", None)
        )
        self.remote_pcap_pattern = PcapFilePattern(
            kwargs.pop("remote_pcap_pattern", None)
        )
        self.tests_generated = list()

    def __iter__(self):
        for i, (in_ml, out_ml) in self.ml_iterator:
            if in_ml.is_deterministic() and out_ml.is_deterministic():
                repeat = 1
            else:
                repeat = 100

            for j in range(repeat):
                test = TestCase(
                    in_ml=in_ml,
                    out_ml=out_ml,
                    cmd=self.cmd_pattern.format(i=i, j=j),
                    stdout=self.stdout_pattern.get(i, j),
                    stderr=self.stderr_pattern.get(i, j),
                    local_pcap=self.local_pcap_pattern.get(i, j),
                    remote_pcap=self.remote_pcap_pattern.get(i, j)
                )
                self.tests_generated.append(test)
                yield test
                # The files must be closed right after being used
                # to avoid keeping too many file descriptors opened
                self.stdout_pattern.close(i, j)
                self.stderr_pattern.close(i, j)

        # Closing all remaining files for safety
        self.stdout_pattern.close_all()
        self.stderr_pattern.close_all()
