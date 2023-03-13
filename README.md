# About
A python project to help find the optimal MTU values that maximizes the upload or download speeds between a peer and server. It also helps find bandwidth dead zones caused due to a poor choice of MTUs.

I built the project to help myself find the right MTU values for my WG server and peer. I inadvertently found that the default MTU values for the server and peer in my case put my WG connection in a bandwidth dead zone. [Related reddit post](https://www.reddit.com/r/WireGuard/comments/plm8y7/finding_the_optimal_mtu_for_wg_server_and_wg_peer/).

You can have a look at the real-world heatmaps which are posted by users in the issue [Post your MTU heatmaps here!](https://github.com/nitred/nr-wg-mtu-finder/issues/4) If you happen to successfully use `nr-wg-mtu-finder` and are able to generate a heatmap, please post your heatmap in the issue if possible. 


***Lastly, please read the following documentation carefully!***

* Read the *WARNING* section!
* This project offers no warranties, therefore do not use it in production. Ideally trying using two VMs that are similar to your production setup.
* The project was developed and tested against a WG peer and WG server running Ubuntu 20.04.
    * Additionally the project only supports `python 3.8` and `python 3.9`. While it may work on `python 3.7` and `python 3.10`, you may have to resolve some issues with building depedencies, yourself.  


#### Project Version
```
0.2.1
```


# Example Bandwidth Plot
* Light green and white areas indicate good to optimal MTU values.
* Green areas indicate bad MTU values.
* Dark green areas are dead zones.

![Bandwidth Plot](./examples/example.png)

# Warning
***WARNING: This project contains scripts that run shell commands using root access. DO NOT USE IN PRODUCTION.***

***WARNING: This project tears down and spins up the Wireguard interface in the order of a thousand times. DO NOT USE IN PRODUCTION.***

That being said, if you're an experienced python developer, please go through the code to verify that it meets your security standards.


# Installation

The project has been built and tested on  


Install the following on both the WG server and WG peer

For MacOS you can use Homebrew to install all of the dependencies.
* Install `ping`
    ```bash
    sudo apt install iputils-ping
    ```
* Install `iperf3`
    ```bash
    sudo apt install iperf3
    ```
* Install `sed`
    ```bash
    # Ubuntu
    sudo apt install sed
    # MacOS. You need to install gnu-sed to be compatible with this package. You might also need to path it properly like this `PATH="/opt/homebrew/opt/gnu-sed/libexec/gnubin:$PATH"`
    brew install gnu-sed
    ```
* Install `wg-quick`
    ```bash
    # Should come installed when you install Wireguard
    ```
* Install the project
    ```bash
    # Use your environment manager of choice like virtualenv or conda or poetry to pre-create an environment
    pip install nr-wg-mtu-finder==0.2.1 --upgrade
    ```

# Usage

### Prerequisites
1. Follow the installation instructions above for both WG server and WG peer
1. The project assumes that you already have a working WG installation on both the WG peer and WG server.
1. The project assumes that you already have a WG interface like `wg0`.
1. The project assumes that you already have a WG conf file like `/etc/wireguard/wg0.conf`. ***Take a backup of these files***.
1. Before running the following scripts, the WG interface is expected to be active/online such that the peer is able to ping the server. Use `wg-quick up INTERFACE` on both the WG server and WG peer to activate the connection.
1. Start the WG server script before the WG peer script

### On the WG Server
1. Let your firewall accept connections on port 5201 from IPs within your WG interface. This port is used by the iperf3 server.
   ```text
   # Replace 10.2.0.0/24 with your interface's IP range
   ufw allow proto tcp from 10.2.0.0/24 to any port 5201
   ```
1. Let your firewall accept connections on port 5000 from IPs within your WG interface. This port is used by the flask server.
   ```text
   # Replace 10.2.0.0/24 with your interface's IP range
   ufw allow proto tcp from 10.2.0.0/24 to any port 5000
   ```
1. Add the MTU setting to the WG conf file i.e. `/etc/wireguard/wg0.conf`. Choose any random MTU, it will be replaced by the script anyway:
    ```text
    [Interface]
    ...
    MTU = 1420  # <----- ADD THIS LINE IF NOT ALREADY EXISTS

    [Peer]
    ...
    ```
1. Start the server script with the following command.
    ```bash
    # Example: The script cycles server MTUs from 1280 to 1290 in steps of 2
    nr-wg-mtu-finder --mode server --mtu-min 1280 --mtu-max 1290 --mtu-step 2 --server-ip 10.2.0.1
    ```

### On the WG Peer
1. Add the MTU setting to the WG conf file i.e. `/etc/wireguard/wg0.conf`. Choose any random MTU, it will be replaced by the script anyway:
    ```text
    [Interface]
    ...
    MTU = 1420  # <----- ADD THIS LINE IF NOT ALREADY EXISTS

    [Peer]
    ...
    ```
1. Start the server script with the following command.
    ```bash
    # Example: The script cycles peer MTUs from 1280 to 1290 in steps of 2
    nr-wg-mtu-finder --mode peer --mtu-min 1280 --mtu-max 1290 --mtu-step 2 --server-ip 10.2.0.1
    ```

# How it works?

* Two python scripts need to be running simultaneously, one of the WG server and one on the WG peer. Let's call them *server script* and *peer script*.
* The both scripts use `subprocess.Popen` to run shell commands. The following commands are used and expected to be pre-installed if not already available:
    * `ping`
    * `iperf3`
    * `wg-quick`
    * `sed`
* The server script also runs a `flask` server and the peer script uses `requests` to communicate with the flask server.


### How does the server script work?
1. The flow for the server script is defined in the method `MTUFinder.run_server_mode()`.
1. First, a flask server called a `sync_server` is run is the background on a separate process.
    * The `sync_server's` listens for requests and commands from the peer script so that they can synchronize with each other.
    * The peer script waits for the `sync_server` to be available before running any upload or download tests.
    * The peer scripts get the status and MTU of the server script from the `sync_server`.
    * The peer script tells the `sync_server` that it is done with its cycling through all of its MTUs and is ready for the server script to change its MTU so that it can start a fresh cycle.
    * The `sync_server` informs the peer script that the server script is finished with cycling through all MTUs and that it is going to shut itself down. The peer script uses this signal to shut itself down as well.
1. When the server script receives an `INTIALIZE` signal, it runs the following shell commands
    * First, terminate an `iperf3` server process if it is already running.
    * Spin down the WG interface
        ```
        wg-quick down wg0
        ```
    * Replace the MTU in the WG conf file with the next MTU in the list
        ```
        # 1421 is the new MTU
        sed -i s/MTU.*/MTU = 1421/ /etc/wireguard/wg0.conf
        ```
    * Spin up the WG interface
        ```
        wg-quick up wg0
        ```
    * Run iperf3 in server mode
        ```
        iperf3 -s
        ```
1. If the server has finishing cycling through all of its MTUs and then receives a request from peer script that it is ready for a new cycle, then the server sends a `SHUTDOWN` signal to the peer script via the `sync_server`.


### How does the peer script work?
* On start, the peer script checks if the `sync_server` is reachable. Once it is reachable, it sends a `peer/ready` request to the server script.
* The peer script then waits for the `iperf3` server to start on the server side. Once it recognizes that the iperf3 server has started, and then the peer script starts cycling through each of its MTUs.
    * For each MTU, the peer script runs an upload and download test using the following command
        ```
        # Upload test
        iperf3 -c 10.2.0.1 -J -t 5 -i 5
        # Download test
        iperf3 -c 10.2.0.1 -J -t 5 -i 5 -R
        ```
    * After each download and upload test, the peer script parses the output and stores the bandwidth results in a bandwidth log file.
* Once the peer script is finished cycling through all of its MTU, it sends another `peer/ready` request to the server script and restarts the whole process again with the next server MTU.
* If the server script is finished cycling through all of its MTUs, then it sends a `SHUTDOWN` signal to the peer script as a reply to the `peer/ready` request. The server shuts down after a short delay as does the peer script.
* Finally, the user can check the bandwidth log file to see the results.


### How is the MTU heatmap generated?
* If you successfully ran the server & peer script as described in the instructions, then a log file (csv file) which contains the MTU data like in this [example.csv](https://github.com/nitred/nr-wg-mtu-finder/blob/master/examples/example.csv) is generated by the ***peer script***.
* The filename for this log file looks like `wg_mtu_finder_peer_20220101T000000.csv` and is generated in the same directory where the ***peer script*** was run.
* Once the ***peer script*** is done or is shutting down, then the plot function is called which reads the contents of log csv file and generates a heatmap graph which is written to a png file like in this [example.png](https://github.com/nitred/nr-wg-mtu-finder/blob/master/examples/example.png).
* The filename for the heatmap png looks like `wg_mtu_finder_peer_20220101T000000.png` and is generated in the same directory where the ***peer script*** was run.

So if you successfully ran the server and peer script, you should find two new files (csv + png) generated in the same directory where you ran the ***peer script*** on the ***WG-peer*** server.

# CLI Options

#### nr-wg-mtu-finder
```
$ nr-wg-mtu-finder --help
usage: nr-wg-mtu-finder [-h] --mode MODE --mtu-min MTU_MIN --mtu-max MTU_MAX --mtu-step
                        MTU_STEP --server-ip SERVER_IP [--server-port SERVER_PORT]
                        [--interface INTERFACE] [--conf-file CONF_FILE]
                        [--peer-skip-errors PEER_SKIP_ERRORS]

nr-wg-mtu-finder - Helps find the optimal Wireguard MTU between a WG Server and a WG Peer.

optional arguments:
  -h, --help            show this help message and exit
  --mode MODE           Mode should be 'server' if you are running this script on the WG
                        Server. Mode should be 'peer' if you are running this script on
                        the WG Peer.
  --mtu-min MTU_MIN     Min MTU. Must be in the range [1280, 1500].
  --mtu-max MTU_MAX     Max MTU. Must be in the range [1280, 1500].
  --mtu-step MTU_STEP   By how much to increment the MTU between loops.
  --server-ip SERVER_IP
                        The IP address of the WG server and flask server.
  --server-port SERVER_PORT
                        The port for the flask server.
  --interface INTERFACE
                        The WG interface name. Default: 'wg0'
  --conf-file CONF_FILE
                        The path to the interface config file. Default:
                        '/etc/wireguard/wg0.conf'
  --peer-skip-errors PEER_SKIP_ERRORS
                        Skip errors when known errors occur in 'peer' mode during the MTU
                        loop. The known errors are logged and the loop continues without
                        crashing. Default: 'True'. Example usage: --peer-skip-errors False


```

#### nr-wg-mtu-finder-heatmap
```
$ nr-wg-mtu-finder-heatmap --help
usage: nr-wg-mtu-finder-heatmap [-h] --log-filepath LOG_FILEPATH --heatmap-filepath
                                HEATMAP_FILEPATH

nr-wg-mtu-finder-heatmap - Generate a heatmap file (png) from a log file (csv) that was
created by the `nr-wg-mtu-finder` script. This is useful in case the original script file
crashed midway.

optional arguments:
  -h, --help            show this help message and exit
  --log-filepath LOG_FILEPATH
                        Absolute path to the log file (csv) that was created by the `nr-wg-
                        mtu-finder` script.
  --heatmap-filepath HEATMAP_FILEPATH
                        Absolute path to the heatmap file (png) which will be created from
                        the log file (csv).
         
```

# Development

### Publish to pypi.org
* Bump version
* `pip install poetry==1.1.15`
* `poetry build`
* `poetry publish --dry-run`

# License
MIT
