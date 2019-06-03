"""Runs the test suite based on the config of the user.

The `Engine` is the main engine for fragscapy. It is used to setup the
Netfilter rules, generate the mod lists, run the test suite and cleanup
everything at the end.

The `EngineThread` is a thread in charge of modifying the intercept packets
and sending them back to the network.
"""

import itertools
import subprocess
import threading
import warnings

import tqdm

from fragscapy.modgenerator import ModListGenerator
from fragscapy.netfilter import NFQueue, NFQueueRule
from fragscapy.packetlist import PacketList


STDOUT_FILE = "stdout{i}.txt"     # Redirect stdout to this file
STDERR_FILE = "stderr{i}.txt"     # Redirect stderr to this file
MODIF_FILE = "modifications.txt"  # Details of each mod on this file


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
        *args: The args passed to the `Thread` class.
        **kwargs: The kwargs passed to the `Thread` class.

    Examples:
        Assuming the nfqueue, modlist1, modlist2 and modlist3 objects exists

        >>> engine_th = EngineThread(nfqueue, modlist1, modlist2)
        >>> engine_th.start()        # Start processing the packets
        >>> engine_th.input_modlist  # Thread-safe copy of the input modlist
        >>> engine_th.output_modlist = modlist3  # Thread-safe modification
    """

    def __init__(self, nfqueue, *args, input_modlist=None, output_modlist=None,
                 **kwargs):
        super(EngineThread, self).__init__(*args, **kwargs)
        self._nfqueue = nfqueue
        self._input_modlist = input_modlist
        self._output_modlist = output_modlist
        self._input_lock = threading.Lock()
        self._output_lock = threading.Lock()

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
            # Mangle the packet to the NFQUEUE (so it is sent
            # correctly to the local application)
            packet.mangle()

    def _process_output(self, packet):
        """Applies the output modifications on `packet`."""
        # Put the packet in a packet list
        packetlist = PacketList()
        packetlist.add_packet(packet.scapy_pkt)

        with self._output_lock:
            packetlist = self._output_modlist.apply(packetlist)

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

    Args:
        config (:obj:`Config`): The configuration to use to get all the
            necessary data.
        progressbar (bool, optional): Show a progressbar during the process.
            Default is 'True'.
        modif_file (str, optional): The filename where to write the
            modifications. Default is 'modifications.txt'.
        stdout_file (str, optional): The filename where to redirect stdout.
            Use the formating '{i}' to have a different file for each test.
            Default is 'stdout{i}.txt'.
        stderr_file (str, optional): The filename where to redirect stderr.
            Use the formating '{i}' to have a different file for each test.
            Default is 'stderr{i}.txt'.

    Attributes:
        progressbar (bool): Shows a progressbar during the process if True.
        modif_file (str, optional): The filename where to write the
            modifications. Default is 'modifications.txt'.
        stdout_file (str, optional): The filename where to redirect stdout.
            Use the formating '{i}' to have a different file for each test.
            Default is 'stdout{i}.txt'.
        stderr_file (str, optional): The filename where to redirect stderr.
            Use the formating '{i}' to have a different file for each test.
            Default is 'stderr{i}.txt'.

    Examples:
        >>> engine = Engine(Config("my_conf.json"))
        >>> engine.start()
        100%|████████████████████████████| 200/200 [00:00<00:00, 21980.42it/s]

        >>> engine = Engine(Config("my_conf.json"), progressbar=False)
        >>> engine.start()
    """

    # Template of the infos for each modification
    MODIF_TEMPLATE = ("Modification n°{i}:\n"
                      "> INPUT:\n"
                      "{input_modlist}\n"
                      "\n"
                      "> OUTPUT:\n"
                      "{output_modlist}\n"
                      "=================================================="
                      "\n"
                      "\n")

    # pylint: disable=too-many-arguments
    def __init__(self, config, progressbar=True, modif_file=MODIF_FILE,
                 stdout_file=STDOUT_FILE, stderr_file=STDERR_FILE):
        self.progressbar = progressbar
        self.modif_file = modif_file
        self.stdout_file = stdout_file
        self.stderr_file = stderr_file

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
                output_modlist=self._mlgen_output[0]
            ))

    def _write_modlist_to_file(self, i, input_modlist, output_modlist):
        """Writes the modification details to the 'modif_file'."""
        with open(self.modif_file, "a") as mod_file:
            mod_file.write(self.MODIF_TEMPLATE.format(
                i=i,
                input_modlist=input_modlist,
                output_modlist=output_modlist
            ))

    def _update_modlists(self, i, input_modlist, output_modlist):
        """Changes the modlist in all the threads."""
        for engine_thread in self._engine_threads:
            engine_thread.input_modlist = input_modlist
            engine_thread.output_modlist = output_modlist
        self._write_modlist_to_file(i, input_modlist, output_modlist)

    def _run_cmd(self, i):
        """Launches the user command in a sub-process.

        Redirect stdout and stderr to the corresponding files.

        Args:
            i: current iteration number, used for formating the filenames.
        """
        fout = self.stdout_file.format(i=i)
        ferr = self.stderr_file.format(i=i)
        with open(fout, "ab") as out, open(ferr, "ab") as err:
            subprocess.run(self._cmd, stdout=out, stderr=err, shell=True)

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
        self._insert_nfrules()
        self._start_threads()

    def run(self):
        """Runs the test suite.

        Generates a modlist, run the command and do it over and over until all
        the possible modlists are exhausted.
        """
        iterator = self._get_modlist_iterator()

        for i, (input_modlist, output_modlist) in iterator:
            # Change the modlist in the threads
            self._update_modlists(i, input_modlist, output_modlist)
            # Run the command
            self._run_cmd(i)

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
        iterator = self._get_modlist_iterator()
        for i, (input_modlist, output_modlist) in iterator:
            self._write_modlist_to_file(i, input_modlist, output_modlist)
