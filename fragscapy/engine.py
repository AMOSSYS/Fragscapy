"""
The main engine for fragscapy. It is used to start everything in order to
intercept packet, modify them and send the modified version.
"""
from threading import Thread, Lock
import warnings
import subprocess
from itertools import product
from tqdm import tqdm

from .modgenerator import ModListGenerator
from .netfilter import NFQueue, NFQueueRule
from .packetlist import PacketList


class EngineError(ValueError):
    """ An Error during the execution of the engine. """
    pass


class EngineWarning(Warning):
    """ Warning during the execution of the engine. """
    pass


def engine_warning(msg):
    """ Raises a warning about the engine, details in `msg`. """
    warnings.warn(
        "{}".format(msg),
        EngineWarning
    )


class EngineThread(Thread):
    """
    A thread that, once started, catches and transform the packet in the
    NFQUEUE. The thread applies the `input_modlist` (resp. the
    `output_modlist`) to the packets caught on the INPUT chain (resp. the
    OUTPUT chain).

    These two mod lists can be thread-safely replaced at any time.

    >>> # Assuming the nfqueue, modlist1, modlist2 and modlist3 objects exists
    >>> engine_th = EngineThread(nfqueue, modlist1, modlist2)
    >>> engine_th.start()        # Start processing the packets
    >>> engine_th.input_modlist  # Thread-safe copy of the input modlist
    >>> engine_th.output_modlist = modlist3  # Thread-safe modification

    :param nfqueue: The `NFQueue` object used to catch the packet
    :param input_modlist: The `ModList` to use on packet on the INPUT chain.
        If not set, it should be set later and before starting the thread
    :param output_modlist: The `ModList` to use on packet on the OUTPUT chain.
        If not set, it should be set later and before starting the thread
    :param args: The args passed to the `Thread` class
    :param kwargs: The kwargs passed to the `Thread` class
    """
    def __init__(self, nfqueue, *args, input_modlist=None, output_modlist=None,
                 **kwargs):
        super(EngineThread, self).__init__(*args, **kwargs)
        self.nfqueue = nfqueue
        self._input_modlist = input_modlist
        self._output_modlist = output_modlist
        self._input_lock = Lock()
        self._output_lock = Lock()

    @property
    def input_modlist(self):
        """ The modlist applied to the packets on INPUT chain. """
        with self._input_lock:
            return self._input_modlist.copy()

    @input_modlist.setter
    def input_modlist(self, new):
        with self._input_lock:
            self._input_modlist = new

    @property
    def output_modlist(self):
        """ The modlist applied to the packets on OUTPUT chain. """
        with self._output_lock:
            return self._output_modlist.copy()

    @output_modlist.setter
    def output_modlist(self, new):
        with self._output_lock:
            self._output_modlist = new

    def _process_input(self, packet):
        """ Apply the input modifications on `packet`. """
        # Put the packet in a packet list
        packetlist = PacketList()
        packetlist.add_packet(packet._scapy_pkt)

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
            packet.set_scapy(packetlist[0].pkt)
            # Mangle the packet to the NFQUEUE (so it is sent
            # correctly to the local application)
            packet.mangle()

    def _process_output(self, packet):
        """ Apply the output modifications on `packet`. """
        # Put the packet in a packet list
        packetlist = PacketList()
        packetlist.add_packet(packet._scapy_pkt)

        with self._output_lock:
            packetlist = self._output_modlist.apply(packetlist)

        # Send all the packets resulting
        packetlist.send_all()
        # Drop the old packet in NFQUEUE
        packet.drop()

    def run(self):
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
        for packet in self.nfqueue:
            if packet.is_input:
                self._process_input(packet)
            else:
                self._process_output(packet)

        return None



class Engine:
    """
    Main engine to run fragscapy, given a `Config` object.

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
    (input and output) from the `ModListGenerator`s, set thoses in the threads
    that process the packets and run the command that was specified in the
    config. It then loops back to generating the next `ModList`s.

    :param config: The `Config` object to use to get all the necessary data.
    :param progressbar: Show a progressbar during the process. Default: True.
    """
    STDOUT_FILE = "stdout{i}.txt"     # Redirect stdout to this file
    STDERR_FILE = "stderr{i}.txt"     # Redirect stderr to this file
    MODIF_FILE = "modifications.txt"  # Details of each mod on this file
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

    def __init__(self, config, progressbar=True):
        self.progressbar = progressbar

        # The cartesian product of the input and output `ModListGenerator`
        self.modlist_input_generator = ModListGenerator(config.input)
        self.modlist_output_generator = ModListGenerator(config.output)

        # The command to run
        self.cmd = config.cmd

        # Populate the NFQUEUE-related objects
        self.nfrules = list()
        self.nfqueues = list()
        for nfrule in config.nfrules:
            self.nfrules.append(NFQueueRule(**nfrule))
            qnum = nfrule.get('qnum', 0)
            if not qnum % 2:
                self.nfqueues.append(NFQueue(qnum=qnum))

        # Prepare the threads that catches, modify and send the packets
        self.engine_threads = list()
        for nfqueue in self.nfqueues:
            self.engine_threads.append(EngineThread(
                nfqueue,
                input_modlist=self.modlist_input_generator[0],
                output_modlist=self.modlist_output_generator[0]
            ))

    def _update_modlists(self, i, input_modlist, output_modlist):
        """ Change the modlist in all the threads. """
        for engine_thread in self.engine_threads:
            engine_thread.input_modlist = input_modlist
            engine_thread.output_modlist = output_modlist
        # Write the modification details to the MODIF_FILE
        with open(self.MODIF_FILE, "w+") as mod_file:
            mod_file.write(self.MODIF_TEMPLATE.format(
                i=i,
                input_modlist=input_modlist,
                output_modlist=output_modlist
            ))

    def _run_cmd(self, i):
        """
        Launch the user command in a sub-process and redirect stdout and
        stderr to the corresponding files.
        """
        fout = self.STDOUT_FILE.format(i=i)
        ferr = self.STDERR_FILE.format(i=i)
        with open(fout, "wb") as out, open(ferr, "wb") as err:
            subprocess.run(self.cmd, stdout=out, stderr=err, shell=True)

    def pre_run(self):
        """ All the actions that need to be run before the Engine starts. """
        for nfrule in self.nfrules:
            nfrule.insert()
        for engine_thread in self.engine_threads:
            engine_thread.start()

    def run(self):
        """
        The main action of the engine. Generates a modlist, run the command
        and do it over and over until all the modlists are exhausted.
        """
        iterator = enumerate(product(
            self.modlist_input_generator,
            self.modlist_output_generator
        ))
        if self.progressbar:  # Use tqdm for showing progressbar
            iterator = tqdm(iterator)

        for i, (input_modlist, output_modlist) in iterator:
            # Change the modlist in the threads
            self._update_modlists(i, input_modlist, output_modlist)
            # Run the command
            self._run_cmd(i)

    def post_run(self):
        """ All the actions that need to be run after the Engine stops. """
        for nfrule in self.nfrules:
            nfrule.remove()
        for engine_thread in self.engine_threads:
            engine_thread.join()

    def start(self):
        """ Start the testing with .pre_run(), .run() and .post_run(). """
        self.pre_run()
        self.run()
        self.post_run()
