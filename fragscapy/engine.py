"""Runs the test suite based on the config of the user.

The `Engine` is the main engine for fragscapy. It is used to setup the
Netfilter rules, generate the mod lists, run the test suite and cleanup
everything at the end.

The `EngineThread` is a thread in charge of modifying the intercept packets
and sending them back to the network.
"""

import itertools
import threading
import warnings

import scapy.utils
import tqdm

from fragscapy.modgenerator import ModListGenerator
from fragscapy.netfilter import NFQueue, NFQueueRule
from fragscapy.packetlist import PacketList
from fragscapy.tests import TestSuite


MODIF_FILE = "modifications.txt"   # Details of each mod on this file


class EngineError(ValueError):
    """An Error during the execution of the engine."""


class EngineWarning(Warning):
    """Warning during the execution of the engine."""


def engine_warning(msg):
    """Raises a warning about the engine, details in `msg`."""
    warnings.warn(
        "{}".format(msg),
        EngineWarning
    )


def _append_to_display_list(display_list, i, j, limit):
    """Utility function to add the test i_j to the list that will be displayed
    within the limit given."""
    if len(display_list) < limit:
        display_list.append("n°{}_{}".format(i, j))
    elif len(display_list) == limit:
        display_list.append("...")


# pylint: disable=too-many-instance-attributes
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

    Examples:
        Assuming the nfqueue, modlist1, modlist2 and modlist3 objects exists

        >>> engine_th = EngineThread(nfqueue, modlist1, modlist2)
        >>> engine_th.start()        # Start processing the packets
        >>> engine_th.input_modlist  # Thread-safe copy of the input modlist
        >>> engine_th.output_modlist = modlist3  # Thread-safe modification
    """

    def __init__(self, nfqueue, *args, **kwargs):
        self._nfqueue = nfqueue
        self._nfqueue_lock = threading.RLock()
        self._input_modlist = kwargs.pop("input_modlist", None)
        self._output_modlist = kwargs.pop("output_modlist", None)
        self._input_lock = threading.Lock()
        self._output_lock = threading.Lock()
        self._local_pcap = kwargs.pop("local_pcap", None)
        self._remote_pcap = kwargs.pop("remote_pcap", None)
        self._local_pcap_lock = threading.Lock()
        self._remote_pcap_lock = threading.Lock()
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

    @property
    def local_pcap(self):
        """A pcap file where the packets of the local side should be dumped
        to. 'None' means the packets are not dumped. Read/Write is
        thread-safe."""
        with self._local_pcap_lock:
            return self._local_pcap

    @local_pcap.setter
    def local_pcap(self, new):
        with self._local_pcap_lock:
            self._local_pcap = new

    @property
    def remote_pcap(self):
        """A pcap file where the packets of the remote side should be dumped
        to. 'None' means the packets are not dumped. Read/Write is
        thread-safe."""
        with self._remote_pcap_lock:
            return self._remote_pcap

    @remote_pcap.setter
    def remote_pcap(self, new):
        with self._remote_pcap_lock:
            self._remote_pcap = new

    def _process_input(self, packet):
        """Applies the input modifications on `packet`."""
        # Dump the packet before anything else
        if self.remote_pcap is not None:
            scapy.utils.wrpcap(self.remote_pcap, packet.scapy_pkt,
                               append=True)

        # Checks that the INPUT modlist is populated
        with self._input_lock:
            if self._input_modlist is None:
                raise EngineError(
                    "Can't run the engine with no INPUT modlist"
                )

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

        # Checks that the OUTPUT modlist is populated
        with self._output_lock:
            if self._output_modlist is None:
                raise EngineError(
                    "Can't run the engine with no OUTPUT modlist"
                )

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
        # Process the queue infinitely
        if not self.is_stopped():
            for packet in self._nfqueue:
                with self._nfqueue_lock:
                    if self.is_stopped():
                        break
                    if packet.is_input:
                        self._process_input(packet)
                    else:
                        self._process_output(packet)

    def is_stopped(self):
        """Has the thread been stopped ?"""
        with self._nfqueue_lock:
            return self._nfqueue.is_stopped()

    def stop(self):
        """Stops the thread by stopping the nfqueue processing."""
        with self._nfqueue_lock:
            self._nfqueue.stop()


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
        dsiplay_results (bool, optional): Display the results at the end of
            the tests. Default is 'True'.
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
        diplay_results (bool): Display the results at the end of the tests if
            True.
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
    MODIF_TEMPLATE = (
        "Modification n°{i}{repeat}:\n"
        "> INPUT:\n"
        "{input_modlist}\n"
        "\n"
        "> OUTPUT:\n"
        "{output_modlist}\n"
        "=================================================="
        "\n"
        "\n"
    )
    # Template used to display the results
    RESULTS_TEMPLATE = (
        "Results ({nb_tests} tests done over {nb_mods} scenarios)\n"
        "==================\n"
        "Pass : {nb_passed}\n"
        "    {display_passed}\n"
        "Fail : {nb_failed}\n"
        "    {display_failed}\n"
        "Not Done : {nb_not_done}\n"
        "    {display_not_done}"
    )


    def __init__(self, config, **kwargs):
        self.progressbar = kwargs.pop("progressbar", True)
        self.display_results = kwargs.pop("display_results", True)

        # Build the generator for all mods
        in_ml = ModListGenerator(config.input)
        out_ml = ModListGenerator(config.output)
        ml_iterator = itertools.product(in_ml, out_ml)
        if self.progressbar:  # Use tqdm for showing progressbar
            ml_iterator = tqdm.tqdm(ml_iterator, total=len(in_ml)*len(out_ml))

        # The test suite object
        self.test_suite = TestSuite(
            ml_iterator=ml_iterator,
            cmd_pattern=config.cmd,
            modif_file_pattern=kwargs.pop("modif_file", MODIF_FILE),
            stdout="stdout" in kwargs,
            stdout_pattern=kwargs.pop("stdout", None),
            stderr="stderr" in kwargs,
            stderr_pattern=kwargs.pop("stderr", None),
            local_pcap_pattern=kwargs.pop("local_pcap", None),
            remote_pcap_pattern=kwargs.pop("remote_pcap", None)
        )
        self.append = kwargs.pop("append", False)

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
            self._engine_threads.append(EngineThread(nfqueue))

    def _write_modlist_to_file(self, repeated_test_case):
        """Writes the modification details to the 'modif_file'."""
        repeat = ("(repeated {} times)".format(repeated_test_case.repeat)
                  if repeated_test_case.repeat > 1
                  else "")
        with open(repeated_test_case.modif_file, "a") as mod_file:
            mod_file.write(self.MODIF_TEMPLATE.format(
                i=repeated_test_case.test_id,
                repeat=repeat,
                input_modlist=repeated_test_case.input_modlist,
                output_modlist=repeated_test_case.output_modlist
            ))

    def _update_modlists(self, repeated_test_case):
        """Changes the modlist in all the threads."""
        for engine_thread in self._engine_threads:
            engine_thread.input_modlist = repeated_test_case.input_modlist
            engine_thread.output_modlist = repeated_test_case.output_modlist
        self._write_modlist_to_file(repeated_test_case)

    def _update_pcap_files(self, test_case):
        """Changes the pcap files in all the threads."""
        for engine_thread in self._engine_threads:
            engine_thread.local_pcap = test_case.local_pcap
            engine_thread.remote_pcap = test_case.remote_pcap

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

    def _stop_threads(self):
        """Send the signal to stop the threads used to process the packets."""
        for engine_thread in self._engine_threads:
            engine_thread.stop()

    def _join_threads(self):
        """Joins the engine threads used to process the packets."""
        for engine_thread in self._engine_threads:
            engine_thread.join()

    def pre_run(self):
        """Runs all the actions that need to be run before `.run()`."""
        if not self.append:
            self.test_suite.flush_all_files()
        self._insert_nfrules()
        self._start_threads()

    def run(self):
        """Runs the test suite.

        Generates a modlist, run the command and do it over and over until all
        the possible modlists are exhausted.
        """
        for repeated_test_case in self.test_suite:
            self._update_modlists(repeated_test_case)
            for test_case in repeated_test_case:
                self._update_pcap_files(test_case)
                test_case.run()

    def post_run(self):
        """Runs all the actions that need to be run after `.run()`."""
        self._stop_threads()
        self._join_threads()
        self._remove_nfrules()

    def print_results(self):
        """Prints a summary of which test passed and which did not."""
        display_limit = 80 // len("n°ii_j, ")  # Max 80 chars

        nb_tests, nb_mods, nb_passed, nb_failed, nb_not_done = 0, 0, 0, 0, 0
        display_passed = list()
        display_failed = list()
        display_not_done = list()
        for repeated_test_case in self.test_suite.tests_generated:
            nb_mods += 1
            for test_case in repeated_test_case.tests_generated:
                nb_tests += 1
                if test_case.is_success():
                    nb_passed += 1
                    display_list = display_passed
                elif test_case.is_failure():
                    nb_failed += 1
                    display_list = display_failed
                else:
                    nb_not_done += 1
                    display_list = display_not_done
                _append_to_display_list(
                    display_list,
                    repeated_test_case.test_id,
                    test_case.test_id,
                    display_limit
                )

        results = self.RESULTS_TEMPLATE.format(
            nb_tests=nb_tests,
            nb_mods=nb_mods,
            nb_passed=nb_passed,
            display_passed=", ".join(display_passed),
            nb_failed=nb_failed,
            display_failed=", ".join(display_failed),
            nb_not_done=nb_not_done,
            display_not_done=", ".join(display_not_done),
        )
        print(results)

    def start(self):
        """Starts the test suite by running `.pre_run()`, `.run()` and
        finally `.post_run()`."""
        self.pre_run()
        self.run()
        self.post_run()
        if self.display_results:
            self.print_results()

    def check_nfrules(self):
        """Checks that the NF rules should work without errors."""
        self._insert_nfrules()
        self._remove_nfrules()

    def check_modlist_generation(self):
        """Checks that the ModListGenerator will generate all mods."""
        if not self.append:
            self.test_suite.flush_modif_files()
        for repeated_test_case in self.test_suite:
            self._write_modlist_to_file(repeated_test_case)
