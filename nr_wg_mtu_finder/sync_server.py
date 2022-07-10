from typing import Optional

from flask import Flask, jsonify, request
from typing_extensions import Literal

status: Literal["NOT_INITIALIZED", "INITIALIZED", "SHUTDOWN"] = "NOT_INITIALIZED"
mtu: Optional[int] = None


def run_sync_server(host, port, to_server_queue, from_server_queue):
    """Run a flask/http server which is used to synchronize with the Peer script.

    1. Peer can request the flask/http server for Server MTU and its status.
    2. Peer can request the flask/http server to shutdown once the Peer is finished.
    """
    app = Flask(__name__)

    def shutdown_server():
        shutdown = request.environ.get("werkzeug.server.shutdown")
        if shutdown is None:
            raise RuntimeError("Not running with the Werkzeug Server")
        shutdown()

    @app.route("/server/status", methods=["GET"])
    def server_status():
        global mtu, status
        print("RECEIVED REQUEST /server/status")

        msg = None if to_server_queue.empty() else to_server_queue.get()

        if msg:
            # Update global state
            mtu, status = msg["server_mtu"], msg["server_status"]

            if status == "SHUTDOWN":
                # App will shutdown after sending one last response
                shutdown_server()
                from_server_queue.put("SHUTDOWN")
            elif status == "INITIALIZED":
                pass
            else:
                raise NotImplementedError()

            return jsonify({"server_mtu": mtu, "server_status": status})
        else:
            # Return current state
            return jsonify({"server_mtu": mtu, "server_status": status})

    @app.route("/peer/ready", methods=["GET"])
    def peer_ready():
        """Peer is done with its cycle and is waiting for next cycle."""
        global mtu, status
        print("RECEIVED REQUEST /peer/ready")
        status = "NOT_INITIALIZED"

        from_server_queue.put("INITIALIZE")
        return jsonify({"server_mtu": mtu, "server_status": status})

    app.run(host=host, port=port)
