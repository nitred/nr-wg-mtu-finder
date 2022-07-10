import json
import subprocess
import sys
import time
from datetime import datetime

import requests

from nr_wg_mtu_finder.plot import create_heatmap_from_log

# Set to either client or server
from nr_wg_mtu_finder.sync_server import run_sync_server


class ReturncodeError(Exception):
    pass


class MTUFinder(object):
    def __init__(
        self,
        mode,
        server_ip,
        server_port,
        interface,
        conf_file,
        mtu_max,
        mtu_min,
        mtu_step,
        peer_skip_errors,
    ):
        """Init."""
        self.mode = mode

        self.server_ip = server_ip
        self.server_port = server_port
        self.interface = interface
        self.conf_file = conf_file

        self.mtu_max = mtu_max
        self.mtu_min = mtu_min
        self.mtu_step = mtu_step

        self.peer_mtu = None
        self.server_mtu = None
        self.current_mtu = None

        self.peer_skip_errors = peer_skip_errors

        self.log_filepath = (
            f"wg_mtu_finder_{self.mode}_{datetime.now().strftime('%Y%m%dT%H%M%S')}.csv"
        )
        self.heatmap_filepath = (
            f"wg_mtu_finder_{self.mode}_{datetime.now().strftime('%Y%m%dT%H%M%S')}.png"
        )

        if self.mode == "server":
            self.run_server_mode()
        elif self.mode == "peer":
            self.run_peer_mode()
        else:
            raise NotImplementedError()

    def create_log(self):
        """Create an empty CSV log file with the headers.

        This log file will be used to store all bandwidth information for each MTU test.
        """
        msg = f"Creating log file: {self.log_filepath}"
        print(f"{msg:<50s}", end=": ")
        with open(self.log_filepath, "w") as f:
            f.write(
                f"server_mtu,"
                f"peer_mtu,"
                f"upload_rcv_mbps,"
                f"upload_send_mbps,"
                f"download_rcv_mbps,"
                f"download_send_mbps\n"
            )
        print("SUCCESS")

    @staticmethod
    def handle_returncode(returncode, stdout, stderr):
        """Handle status code."""
        if returncode == 0:
            print("SUCCESS")
        else:
            print(f"FAILED with code {returncode}")
            print(f"*" * 80)
            print(f"STDOUT:\n-------")
            print(stdout)
            print(f"STDERR:\n-------")
            print(stderr)
            print(f"*" * 80)
            raise ReturncodeError()

    def append_log_with_bandwidth_info(
        self, up_rcv_bps, up_snd_bps, down_rcv_bps, down_snd_bps
    ):
        """Append the bandwidth information to the log file."""
        if self.mode == "server":
            raise NotImplementedError()

        msg = f"Appending log for MTU: {self.current_mtu}"
        print(f"{msg:<50s}", end=": ")

        with open(self.log_filepath, "a") as f:
            f.write(
                f"{self.server_mtu},"
                f"{self.peer_mtu},"
                f"{up_rcv_bps / 1000000:0.3f},"
                f"{up_snd_bps / 1000000:0.3f},"
                f"{down_rcv_bps / 1000000:0.3f},"
                f"{down_snd_bps / 1000000:0.3f}\n"
            )

        print("SUCCESS")

    def wg_quick_down(self):
        """Spin down the interface using wg-quick."""
        msg = "WG Interface Down"
        print(f"{msg:<50s}", end=": ")
        process = subprocess.Popen(
            ["wg-quick", "down", f"{self.interface}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        stdout, stderr = process.communicate()
        self.handle_returncode(
            returncode=process.returncode, stdout=stdout, stderr=stderr
        )

    def wg_quick_up(self):
        """Spin up the interface using wg-quick."""
        msg = "WG Interface Up"
        print(f"{msg:<50s}", end=": ")
        process = subprocess.Popen(
            ["wg-quick", "up", f"{self.interface}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        stdout, stderr = process.communicate()
        self.handle_returncode(
            returncode=process.returncode, stdout=stdout, stderr=stderr
        )

    def __validate_conf_file(self):
        """Validate that a line `MTU =` exists in the wireguard conf."""
        with open(self.conf_file, "r") as f:
            for line in f.readlines():
                if line.startswith("MTU ="):
                    return

        # If no line starts with "MTU = ", then raise an error.
        raise ValueError(
            f"Expected to find a line that begins with 'MTU =' in {self.conf_file} "
            f"file but it was not found. Please check the README file for instructions "
            f"on how to add the missing line to the wg.conf file."
        )

    def update_mtu_in_conf_file(self):
        """Update the MTU setting in the WG Conf.

        Find a line that starts with 'MTU =***' and replace it with 'MTU = <current_mtu>'
        """
        self.__validate_conf_file()

        msg = f"Setting MTU to {self.current_mtu} in /etc/wireguard/wg0.conf"
        print(f"{msg:<50s}", end=": ")
        process = subprocess.Popen(
            ["sed", "-i", f"s/MTU.*/MTU = {self.current_mtu}/", f"{self.conf_file}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )

        stdout, stderr = process.communicate()
        self.handle_returncode(
            returncode=process.returncode, stdout=stdout, stderr=stderr
        )

    def run_iperf3_upload_test(self):
        """Run iperf3 upload test."""
        msg = f"Running peer upload"
        print(f"{msg:<50s}", end=": ")
        command = ["iperf3", "-c", f"{self.server_ip}", "-J", "-t", "5", "-i", "5"]
        # print(f"command: {' '.join(command)}")
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )

        # Wait iperf3 test to be done.
        stdout, stderr = process.communicate()
        self.handle_returncode(
            returncode=process.returncode, stdout=stdout, stderr=stderr
        )

        # load iperf3 output json which results from the -J flag
        output = json.loads(stdout)
        return (
            output["end"]["streams"][0]["receiver"]["bits_per_second"],
            output["end"]["streams"][0]["sender"]["bits_per_second"],
        )

    def run_iperf3_download_test(self):
        """Run iperf3 upload test."""
        msg = f"Running peer download"
        print(f"{msg:<50s}", end=": ")
        process = subprocess.Popen(
            ["iperf3", "-c", f"{self.server_ip}", "-J", "-t", "5", "-i", "5", "-R"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )

        # Wait iperf3 test to be done.
        stdout, stderr = process.communicate()
        self.handle_returncode(
            returncode=process.returncode, stdout=stdout, stderr=stderr
        )

        # load iperf3 output json which results from the -J flag
        output = json.loads(stdout)
        return (
            output["end"]["streams"][0]["receiver"]["bits_per_second"],
            output["end"]["streams"][0]["sender"]["bits_per_second"],
        )

    def __peer_mode__wait_for_server_init(self):
        """Get server mtu.

        Raises:
            - requests.Timeout, requests.ConnectionError or KeyError if there is
              something wrong with the Flask server running on the WG server.
        """
        while True:
            msg = f"Waiting for server init and status"
            print(f"{msg:<50s}", end=": ")
            try:
                resp = requests.get(
                    f"http://{self.server_ip}:{self.server_port}/server/status",
                    verify=False,
                    timeout=5,
                )

                server_mtu, server_status = (
                    resp.json()["server_mtu"],
                    resp.json()["server_status"],
                )

                if (server_status == "INITIALIZED") or (server_status == "SHUTDOWN"):
                    print(
                        f"SUCCESS, SERVER_MTU: {server_mtu}, "
                        f"SERVER_STATUS: {server_status}"
                    )
                    return server_mtu, server_status
                else:
                    print(f"FAILED, SERVER_STATUS: {server_status}, Retrying...")
                    time.sleep(1)
                    continue
            except requests.exceptions.ConnectTimeout:
                print("FAILED, ConnectTimeout, Retrying...")
                time.sleep(1)
                continue

    def __peer_mode__send_server_peer_ready(self):
        """Send restart signal to flask server and get back server status."""
        msg = f"Send peer ready for next loop to server"
        print(f"{msg:<50s}", end=": ")
        resp = requests.get(
            f"http://{self.server_ip}:{self.server_port}/peer/ready",
            verify=False,
            timeout=5,
        )
        server_mtu, server_status = (
            resp.json()["server_mtu"],
            resp.json()["server_status"],
        )
        print("SUCCESS")
        return server_mtu, server_status

    def __peer_mode__ping_server(self):
        """Ping server to reestablish connection between peer and server.

        After server interface is spun down and spun up again, the peer is not
        guaranteed to be connected to the server. Therefore we force a ping to make
        sure peer sends packets on this network.
        """
        msg = f"Pinging server to establish connection"
        print(f"{msg:<50s}", end=": ")
        process = subprocess.Popen(
            ["ping", "-c", "1", f"{self.server_ip}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )

        stdout, stderr = process.communicate()
        self.handle_returncode(
            returncode=process.returncode, stdout=stdout, stderr=stderr
        )

    def run_peer_mode(self):
        """Run all steps for peer mode.

        IMPORTANT: Peer is the one that logs bandwidth into the log file (csv)
        """
        self.create_log()
        while True:
            # Ping IP address of server to flush connection
            self.__peer_mode__ping_server()

            # Tell server that peer is ready for next loop.
            self.__peer_mode__send_server_peer_ready()

            # Ping IP address of server to flush connection
            self.__peer_mode__ping_server()

            # Start a fresh loop of cycling through all peer MTUs
            # At start, find what the current server_mtu is.
            self.server_mtu, server_status = self.__peer_mode__wait_for_server_init()

            if server_status == "INITIALIZED":
                pass
            elif server_status == "SHUTDOWN":
                print(f"Server has shutdown... Shutting down peer script.")
                print(f"Check final bandwidth log: {self.log_filepath}")
                create_heatmap_from_log(
                    log_filepath=self.log_filepath,
                    heatmap_filepath=self.heatmap_filepath,
                )
                print(f"Check final bandwidth plot: {self.heatmap_filepath}")
                sys.exit(0)
            else:
                raise NotImplementedError()

            for current_mtu in range(self.mtu_min, self.mtu_max + 1, self.mtu_step):
                if self.server_mtu is None:
                    raise NotImplementedError()

                self.current_mtu = current_mtu
                self.peer_mtu = current_mtu

                print("-" * 80)
                self.wg_quick_down()
                self.update_mtu_in_conf_file()
                self.wg_quick_up()

                # Wait a short while after interface is spun up.
                time.sleep(1)

                try:
                    # Ping IP address of server to flush connection
                    self.__peer_mode__ping_server()

                    up_rcv_bps, up_snd_bps = self.run_iperf3_upload_test()
                    time.sleep(1)
                    down_rcv_bps, down_snd_bps = self.run_iperf3_download_test()

                    self.append_log_with_bandwidth_info(
                        up_rcv_bps, up_snd_bps, down_rcv_bps, down_snd_bps
                    )
                except ReturncodeError:
                    if self.peer_skip_errors:
                        print(
                            "Caught ReturncodeError: The --peer-skip-errors flag is "
                            "set to True so this Peer MTU iteration will be skipped. "
                            "Continuing with other peer MTUs. Bandwidth for this MTU "
                            "will be recorded as -1 in the log file (csv)."
                        )
                        self.append_log_with_bandwidth_info(-1, -1, -1, -1)
                    else:
                        print(
                            "Caught ReturncodeError: The --peer-skip-errors flag is "
                            "set to False so the Peer loop will crash. If you wish "
                            "to skip MTUs that raise this error in the future, set the "
                            "--peer-skip-errors flag to True when running the script."
                        )
                        raise

    def run_iperf3_server_test(self):
        """Run iperf3 upload test."""
        msg = f"Running iperf3 server"
        print(f"{msg:<50s}", end=": ")
        process = subprocess.Popen(
            ["iperf3", "-s"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )

        time.sleep(1)
        print("SUCCESS")

        return process

    def run_server_mode(self):
        """Run all steps for server mode."""
        import multiprocessing as mp

        pool = mp.Pool(1)
        manager = mp.Manager()

        to_server_queue = manager.Queue(5)
        from_server_queue = manager.Queue(5)

        pool.apply_async(
            run_sync_server,
            kwds={
                "host": self.server_ip,
                "port": self.server_port,
                "to_server_queue": to_server_queue,
                "from_server_queue": from_server_queue,
            },
        )

        iperf3_server_process = None
        mtu_range = list(range(self.mtu_min, self.mtu_max + 1, self.mtu_step))
        mtu_range_iter = iter(mtu_range)

        while True:
            print("-" * 80)
            # Wait for init command from sync server
            sync_server_status = from_server_queue.get(block=True)

            # Any time a message is received from the sync_server, the iperf3 server
            # must be terminated.
            if iperf3_server_process:
                iperf3_server_process.terminate()

            if sync_server_status == "INITIALIZE":
                # We receive INITIALIZE from the peer but sometimes the connection is
                # spun down too quickly before a response could be sent. Therefore
                # we'll wait for a little while until the request has been handled.
                time.sleep(1)

                try:
                    self.current_mtu = next(mtu_range_iter)
                except StopIteration:
                    # Done with cycling through all MTUs
                    # Send Shutdown signal to the sync_server
                    # And go back to waiting for shutdown signal from sync_server
                    to_server_queue.put(
                        {"server_mtu": self.server_mtu, "server_status": "SHUTDOWN"}
                    )
                    continue

                self.server_mtu = self.current_mtu

                self.wg_quick_down()
                self.update_mtu_in_conf_file()
                self.wg_quick_up()

                iperf3_server_process = self.run_iperf3_server_test()

                # Wait a short while after interface is spun up.
                time.sleep(1)

                to_server_queue.put(
                    {"server_mtu": self.server_mtu, "server_status": "INITIALIZED"}
                )

                # Now wait for peer to ping our server
                # Peer will get a response that tells it that the iperf3 server is
                # ready with the current_mtu.
                # Peer will start cycling through all of its MTUs
                # Peer will send another "init" command if it needs the server to

            elif sync_server_status == "SHUTDOWN":
                time.sleep(2)
                print("Received 'SHUTDOWN' signal from sync server. Shutting down.")
                sys.exit(0)

            else:
                raise NotImplementedError()

        # Code should not reach here.
        raise NotImplementedError()
