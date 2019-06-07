"""Runs the test suite based on the config of the user.

The `Engine` is the main engine for fragscapy. It is used to setup the
Netfilter rules, generate the mod lists, run the test suite and cleanup
everything at the end.

The `EngineThread` is a thread in charge of modifying the intercept packets
and sending them back to the network.
"""

import itertools
import glob
import os
import subprocess
import threading
import warnings

import scapy.utils
import tqdm

from fragscapy.modgenerator import ModListGenerator
from fragscapy.netfilter import NFQueue, NFQueueRule
from fragscapy.packetlist import PacketList


MODIF_FILE = "modifications.txt"   # Details of each mod on this file


class EngineError(ValueError):
    """An Error during the execution of the engine."""
    pass


class EngineWarning(Warning):
    """Warning during the execution of the engine."""
    pass


def engine_warning(msg):
    """Raises a warning about the engine, details in `msg`."""
    warnings.warn(
        "{}".format(msg),
        EngineWarning
    )


class EngineThread(threading.Thread):
    """Thread of the engine modifying the packets in NFQUEUE.

    This thread, once started, catches and transform the packet in the
    NFQUEUE. The thread applies the `input_modlist` (resp. the
    `output_modlist`) to the packets caught on the INPUT chain (resp. the
    OUTPUT chain).

    These two mod lists can be thread-safely replaced at any time.

    Args:
        nfqueue (:obj:`NFQueue`): The NF queue used to catch the packets.
        input_modlist (:obj:`ModList`, optional): The list of modifications to
            apply to the packets on the INPUT chain. If not set, it should be
            set before starting the thread.
        output_modlist (:obj:`ModList`, optional): The list of modifications
            to apply to the packets on the OUTPUT chain. If not set, it should
            be set before starting the thread.
        local_pcap (str, optional): A pcap file where the packets of the local
            side should dumped to. Default is 'None' which means the packets
            are not dumped.
        remote_pcap (str, optional): A pcap file where the packets of the
            remote side should dumped to. Default is 'None' which means the
            packets are not dumped.
        *args: The args passed to the `Thread` class.
        **kwargs: The kwargs passed to the `Thread` class.

    Attributes:
        local_pcap (str): A pcap file where the packets of the local side
            should dumped to. 'None' means the packets are not dumped.
        remote_pcap (str): A pcap file where the packets of the remote side
            should dumped to. 'None' means the packets are not dumped.

    Examples:
        Assuming the nfqueue, modlist1, modlist2 and modlist3 objects exists

        >>> engine_th = EngineThread(nfqueue, modlist1, modlist2)
        >>> engine_th.start()        # Start processing the packets
        >>> engine_th.input_modlist  # Thread-safe copy of the input modlist
        >>> engine_th.output_modlist = modlist3  # Thread-safe modification
    """

    def __init__(self, nfqueue, *args, **kwargs):
        self._nfqueue = nfqueue
        self._input_modlist = kwargs.pop("input_modlist", None)
        self._output_modlist = kwargs.pop("output_modlist", None)
        self.local_pcap = kwargs.pop("local_pcap", None)
        self.remote_pcap = kwargs.pop("remote_pcap", None)
        self._input_lock = threading.Lock()
        self._output_lock = threading.Lock()
        super(EngineThread, self).__init__(*args, **kwargs)

    @property
    def input_modlist(self):
        """The modlist applied to the packets on INPUT chain. Read/Write is
        thread-safe."""
        with self._input_lock:
            return self._input_modlist.copy()

    @input_modlist.setter
    def input_modlist(self, new):
        with self._input_lock:
            self._input_modlist = new

    @property
    def output_modlist(self):
        """The modlist applied to the packets on OUTPUT chain. Read/Write is
        thread-safe."""
        with self._output_lock:
            return self._output_modlist.copy()

    @output_modlist.setter
    def output_modlist(self, new):
        with self._output_lock:
            self._output_modlist = new

    def _process_input(self, packet):
        """Applies the input modifications on `packet`."""
        # Dump the packet before anything else
        if self.remote_pcap is not None:
            scapy.utils.wrpcap(self.remote_pcap, packet.scapy_pkt,
                               append=True)

        # Put the packet in a packet list
        packetlist = PacketList()
        packetlist.add_packet(packet.scapy_pkt)

        with self._input_lock:
            packetlist = self._input_modlist.apply(packetlist)

        pl_len = len(packetlist)

        # Warning if there is creation of a packet (more than 1)
        if pl_len > 1:
            engine_warning(
                "More than 1 packet resulting in the INPUT chain. "
                "Got {} packets in the result. They can't be sent to "
                "the NFQUEUE. Only the first one will be reinserted "
                "to the NFQUEUE.".format(pl_len)
            )

        if pl_len == 0:
            # If there is no packet in the result,
            # Inform libnfqueue to drop the waiting packet
            packet.drop()
        else:
            # If there is at least 1 packet in the result, send it
            # Modify the initial packet with the new content
            packet.scapy_pkt = packetlist[0].pkt
            # Dump the packet just before sending it
            if self.local_pcap is not None:
                scapy.utils.wrpcap(self.local_pcap, packet.scapy_pkt,
                                   append=True)
            # Mangle the packet to the NFQUEUE (so it is sent
            # correctly to the local application)
            packet.mangle()

    def _process_output(self, packet):
        """Applies the output modifications on `packet`."""
        # Dump the packet before anything else
        if self.local_pcap is not None:
            scapy.utils.wrpcap(self.local_pcap, packet.scapy_pkt,
                               append=True)

        # Put the packet in a packet list
        packetlist = PacketList()
        packetlist.add_packet(packet.scapy_pkt)

        with self._output_lock:
            packetlist = self._output_modlist.apply(packetlist)

        # Dump the packets just before sending it
        if self.remote_pcap is not None:
            scapy.utils.wrpcap(
                self.remote_pcap,
                [pkt.pkt for pkt in packetlist],
                append=True
            )
        # Send all the packets resulting
        packetlist.send_all()
        # Drop the old packet in NFQUEUE
        packet.drop()

    def run(self):
        """Runs the main loop of the thread.

        Checks that there are starting input_modlist and output_modlist and
        then starts catching the packet in the NFQUEUE and process them.

        Raises:
            EngineError: There is a modlist (input or output) missing.
        """
        # Checks that the INPUT and OUTPUT modlist are populated
        with self._input_lock:
            if self._input_modlist is None:
                raise EngineError(
                    "Can't run the engine with no INPUT modlist"
                )
        with self._output_lock:
            if self._output_modlist is None:
                raise EngineError(
                    "Can't run the engine with no OUTPUT modlist"
                )

        # Process the queue infinitely
        for packet in self._nfqueue:
            if packet.is_input:
                self._process_input(packet)
            else:
                self._process_output(packet)

        return None


# pylint: disable=too-many-instance-attributes
class Engine(object):
    """Main engine to run fragscapy, given a `Config` object.

    The engine will parse the configuration, extract the necessary
    `NFQueueRule` and `NFQueue` objects. It also extracts the
    `ModListGenerator` for the INPUT and the OUTPUT chain. Finaly, it also
    creates the `EngineThread` that will process the packets thanks to all
    these objects.

    Once the initialisation is done, all the internal objects are ready to be
    started and process the incoming packets. The engine can be started with
    the `.start()` method.

    Once started, the engine set up the NF rules necessary to intercept the
    packets and start the thread(s) that process them.

    The next step of the process, is the main loop that generates 2 `ModList`
    (input and output) from the `ModListGenerator`, set thoses in the threads
    that process the packets and run the command that was specified in the
    config. It then loops back to generating the next `ModList`.

    All the arguments about files can use the formating '{i}' and '{j}' to
    have a different file for each test. They respectively contains the
    id of the current modification and the number of the current iteration
    of the same test (in case of non-deterministic tests). Note the only
    excpetion is 'modif_file' which only accepts '{i}' because it does not
    not change when only '{j}' changes.

    Unless `append=True` is specified, the modif, sdtout and stderr filenames
    that matches the provided patterns are removed before running the test so
    the results are not appended to previous files.

    Args:
        config (:obj:`Config`): The configuration to use to get all the
            necessary data.
        progressbar (bool, optional): Show a progressbar during the process.
            Default is 'True'.
        modif_file (str, optional): The filename where to write the
            modifications. Default is 'modifications.txt'.
        stdout (str, optional): The filename where to redirect stdout.
            If not specified (the default), the output is dropped.
            If set to 'None', the output is redirected to stdout.
        stderr (str, optional): The filename where to redirect stderr.
            If not specified (the default), the error output is
            dropped. If set to 'None', the error output is redirected to
            stderr.
        local_pcap (str, optional): A pcap file where the packets of the local
            side should dumped to. Default is 'None' which means the packets
            are not dumped.
        remote_pcap (str, optional): A pcap file where the packets of the
            remote side should dumped to. Default is 'None' which means the
            packets are not dumped.
        append (bool, optional): If 'True', do not erase the existing files
            (modif, stdout and stderr), append the results to them instead.
            Default is 'False'

    Attributes:
        progressbar (bool): Shows a progressbar during the process if True.
        modif_file (str, optional): The filename where to write the
            modifications.
        stdout (bool): 'False' if stdout of the command should be dropped.
        stdout_file (str): The filename where to redirect stdout.
            'None' means the output is dropped
        stderr (bool): 'False' if stderr of the command should be dropped.
        stderr_file (str): The filename where to redirect stderr.
            'None' means the error output is dropped.
        local_pcap (str): A pcap file where the packets of the local side
            should dumped to. 'None' means the packets are not dumped.
        remote_pcap (str): A pcap file where the packets of the remote side
            should dumped to. 'None' means the packets are not dumped.
        append (bool): If 'True', do not erase the existing files
            (modif, stdout and stderr), append the results to them instead.

    Examples:
        >>> engine = Engine(Config("my_conf.json"))
        >>> engine.start()
        100%|████████████████████████████| 200/200 [00:00<00:00, 21980.42it/s]

        >>> engine = Engine(Config("my_conf.json"), progressbar=False)
        >>> engine.start()
    """

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

    def __init__(self, config, **kwargs):
        self.progressbar = kwargs.pop("progressbar", True)
        self.modif_file = kwargs.pop("modif_file", MODIF_FILE)
        try:
            self.stdout_file = kwargs.pop("stdout")
            self.stdout = True
        except KeyError:
            self.stdout_file = None
            self.stdout = False
        try:
            self.stderr_file = kwargs.pop("stderr")
            self.stderr = True
        except KeyError:
            self.stderr_file = None
            self.stderr = False
        self.local_pcap = kwargs.pop("local_pcap", None)
        self.remote_pcap = kwargs.pop("remote_pcap", None)
        self.append = kwargs.pop("append", False)

        # The cartesian product of the input and output `ModListGenerator`
        self._mlgen_input = ModListGenerator(config.input)
        self._mlgen_output = ModListGenerator(config.output)

        # The command to run
        self._cmd = config.cmd

        # Populate the NFQUEUE-related objects
        self._nfrules = list()
        self._nfqueues = list()
        self._qnums = set()
        for nfrule in config.nfrules:
            self._nfrules.append(NFQueueRule(**nfrule))
            qnum = nfrule.get('qnum', 0)
            if not qnum % 2:
                self._qnums.add(qnum)
        for qnum in self._qnums:
            self._nfqueues.append(NFQueue(qnum=qnum))

        # Prepare the threads that catches, modify and send the packets
        self._engine_threads = list()
        for nfqueue in self._nfqueues:
            self._engine_threads.append(EngineThread(
                nfqueue,
                input_modlist=self._mlgen_input[0],
                output_modlist=self._mlgen_output[0],
                local_pcap=self.local_pcap,
                remote_pcap=self.remote_pcap
            ))

    def _flush_modif_files(self):
        """Delete all the files that match the pattern of `modif_file`."""
        for f in glob.glob(self.modif_file.format(i='*')):
            os.remove(f)

    def _write_modlist_to_file(self, i, input_modlist, output_modlist,
                               repeat=0):
        """Writes the modification details to the 'modif_file'."""
        repeat = "(repeated {} times)".format(repeat) if repeat > 1 else ""
        with open(self.modif_file.format(i=i), "a") as mod_file:
            mod_file.write(self.MODIF_TEMPLATE.format(
                i=i,
                repeat=repeat,
                input_modlist=input_modlist,
                output_modlist=output_modlist
            ))

    def _update_modlists(self, i, input_modlist, output_modlist, repeat=0):
        """Changes the modlist in all the threads."""
        for engine_thread in self._engine_threads:
            engine_thread.input_modlist = input_modlist
            engine_thread.output_modlist = output_modlist
        self._write_modlist_to_file(i, input_modlist, output_modlist,
                                    repeat=repeat)

    def _flush_std_files(self):
        """Delete all the files that match the pattern of `stdout_file` and
        `stderr_file`."""
        for f in glob.glob(self.stdout_file.format(i='*', j='*')):
            os.remove(f)
        for f in glob.glob(self.stderr_file.format(i='*', j='*')):
            os.remove(f)

    def _run_cmd(self, i, j):
        """Launches the user command in a sub-process.

        Redirect stdout and stderr to the corresponding files.

        Args:
            i: current modlist iteration number, used for formating the
                filenames.
            j: current repeat iteration number, used for formating the
                filenames.
        """
        # Can not use with statement here because files may be None
        # so emulates the behavior of a with statement with try/finally

        # Load the files if they exists
        if self.stdout and self.stdout_file is not None:
            fout = open(self.stdout_file.format(i=i, j=j), "ab")
        elif self.stdout:
            fout = None
        else:
            fout = subprocess.PIPE

        if self.stderr and self.stderr_file is not None:
            ferr = open(self.stderr_file.format(i=i, j=j), "ab")
        elif self.stderr:
            ferr = None
        else:
            ferr = subprocess.PIPE

        try:
            # Run the command
            subprocess.run(self._cmd, stdout=fout, stderr=ferr, shell=True)
        finally:
            # Close the files even if there was an exception
            try:
                fout.close()
            except AttributeError:  # fout does not have a `.close()`
                pass
            finally:
                try:
                    ferr.close()
                except AttributeError:  # ferr does not have a `.close()`
                    pass

    def _insert_nfrules(self):
        """Inserts all the NF rules using `ip(6)tables`."""
        for nfrule in self._nfrules:
            nfrule.insert()

    def _remove_nfrules(self):
        """Removes all the NF rules using `ip(6)tables`."""
        for nfrule in self._nfrules:
            nfrule.remove()

    def _start_threads(self):
        """Starts the engine threads used to process the packets."""
        for engine_thread in self._engine_threads:
            engine_thread.start()

    def _join_threads(self):
        """Joins the engine threads used to process the packets."""
        for engine_thread in self._engine_threads:
            engine_thread.join()

    def pre_run(self):
        """Runs all the actions that need to be run before `.run()`."""
        if not self.append:
            self._flush_modif_files()
            self._flush_std_files()
        self._insert_nfrules()
        self._start_threads()

    def run(self):
        """Runs the test suite.

        Generates a modlist, run the command and do it over and over until all
        the possible modlists are exhausted.
        """
        iterator = self._get_modlist_iterator()

        for i, (input_modlist, output_modlist) in iterator:
            # How many times should we repeat the command (for random changes)
            if (input_modlist.is_deterministic()
                    and output_modlist.is_deterministic()):
                repeat = 1
            else:
                repeat = 100
            # Change the modlist in the threads
            self._update_modlists(i, input_modlist, output_modlist, repeat)
            # Run the command
            for j in range(repeat):
                self._run_cmd(i, j)

    def post_run(self):
        """Runs all the actions that need to be run after `.run()`."""
        self._remove_nfrules()
        self._join_threads()

    def start(self):
        """Starts the test suite by running `.pre_run()`, `.run()` and
        finaly `.post_run()`."""
        self.pre_run()
        self.run()
        self.post_run()

    def _get_modlist_iterator(self):
        """Returns an iterator for all the possible combinations of modlists.

        Each value of the iterator is on the following format:
            (int<index>, (ModList<input_modlist>, ModList<output_modlist>))
        If `self.progressbar` is True, automatically add the `tqdm` iterator.
        """
        iterator = enumerate(itertools.product(
            self._mlgen_input,
            self._mlgen_output
        ))
        if self.progressbar:  # Use tqdm for showing progressbar
            # Need to manually specify the total size as enumerate and
            # product fucntion prevent from getting it automatically
            total = (len(self._mlgen_input)
                     * len(self._mlgen_output))
            iterator = tqdm.tqdm(iterator, total=total)

        return iterator

    def check_nfrules(self):
        """Checks that the NF rules should work without errors."""
        self._insert_nfrules()
        self._remove_nfrules()

    def check_modlist_generation(self):
        """Checks that the ModListGenerator will generate all mods."""
        if not self.append:
            self._flush_modif_files()
        iterator = self._get_modlist_iterator()
        for i, (input_modlist, output_modlist) in iterator:
            if (input_modlist.is_deterministic()
                    and output_modlist.is_deterministic()):
                repeat = 1
            else:
                repeat = 100
            self._write_modlist_to_file(i, input_modlist, output_modlist,
                                        repeat=repeat)
