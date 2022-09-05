import argparse
import signal
import sys
import time
from distutils.util import strtobool

from pydantic import BaseModel, StrictInt, StrictStr, root_validator
from typing_extensions import Literal

from .mtu_finder import MTUFinder


def signal_handler(sig, frame):
    """Handle ctrl+c interrupt.

    Without this handler, everytime a ctrl+c interrupt is received, the server shutdowns and
    proceeds to the next iteration in the loop rather than exiting the program altogether.
    """
    print("************Received CTRL-C. Will exit in 1 second************")
    time.sleep(1)
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


class ArgsModel(BaseModel):
    mode: Literal["server", "peer"]
    mtu_min: int
    mtu_max: int
    mtu_step: int

    server_ip: StrictStr
    server_port: int = 5000

    peer_skip_errors: bool = True

    interface: StrictStr = "wg0"
    conf_file: StrictStr = "/etc/wireguard/wg0.conf"

    @root_validator(pre=False)
    def validate(cls, values):
        """Generic validations."""
        mtu_min, mtu_max, mtu_step = (
            values.get("mtu_min", None),
            values.get("mtu_max", None),
            values.get("mtu_step", None),
        )

        if not (1280 <= mtu_min <= 1500):
            raise ValueError(f"mtu_min: {mtu_min} must be in range [1280, 1500].")

        if not (1280 <= mtu_max <= 1500):
            raise ValueError(f"mtu_max: {mtu_max} must be in range [1280, 1500].")

        if not (mtu_min <= mtu_max):
            raise ValueError(
                f"mtu_min: {mtu_min} must be less than or equal to mtu_max: {mtu_max}"
            )

        return values

    class Config:
        orm_mode = True


def setup_args():
    """Setup args."""
    parser = argparse.ArgumentParser(
        description=(
            "nr-wg-mtu-finder - Helps find the optimal Wireguard MTU between "
            "a WG Server and a WG Peer."
        )
    )
    parser.add_argument(
        "--mode",
        help=(
            "Mode should be 'server' if you are running this script on the WG Server. "
            "Mode should be 'peer' if you are running this script on the WG Peer."
        ),
        required=True,
    )
    parser.add_argument(
        "--mtu-min",
        help="Min MTU. Must be in the range [1280, 1500].",
        required=True,
    )
    parser.add_argument(
        "--mtu-max",
        help="Max MTU. Must be in the range [1280, 1500].",
        required=True,
    )
    parser.add_argument(
        "--mtu-step",
        help="By how much to increment the MTU between loops.",
        required=True,
    )
    parser.add_argument(
        "--server-ip",
        help="The IP address of the WG server and flask server.",
        required=True,
    )
    parser.add_argument(
        "--server-port",
        help="The port for the flask server. Default: 5000",
        required=False,
        default=5000,
    )
    parser.add_argument(
        "--interface",
        help="The WG interface name. Default: 'wg0'",
        required=False,
        default="wg0",
    )
    parser.add_argument(
        "--conf-file",
        help="The path to the interface config file. Default: '/etc/wireguard/wg0.conf'",
        required=False,
        default="/etc/wireguard/wg0.conf",
    )
    parser.add_argument(
        "--peer-skip-errors",
        help=(
            "Skip errors when known errors occur in 'peer' mode during the MTU loop. "
            "The known errors are logged and the loop continues without crashing. "
            "Default: 'True'. Example usage: --peer-skip-errors False"
        ),
        required=False,
        default=True,
        type=strtobool,
    )
    args = parser.parse_args()
    return args


def run():
    args = setup_args()
    args = ArgsModel.from_orm(args)

    MTUFinder(**args.dict())
