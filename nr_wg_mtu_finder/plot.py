import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def create_heatmap_from_log(log_filepath, heatmap_filepath):
    f, axes = plt.subplots(nrows=2, ncols=2, figsize=(12, 12))

    df = pd.read_csv(log_filepath)

    ax = axes[0, 0]
    dfx = df.pivot(index="server_mtu", columns="peer_mtu", values="upload_rcv_mbps")
    sns.heatmap(
        dfx.values,
        linewidth=0.5,
        ax=ax,
        cmap="Greens_r",
        xticklabels=list(dfx.columns),
        yticklabels=list(dfx.index),
    )
    ax.tick_params(axis="x", rotation=45)
    ax.tick_params(axis="y", rotation=0)
    ax.set(ylabel="Server MTU", xlabel="Peer MTU")
    ax.set_title("Upload Rcv Bandwidth (Mbps)")
    ax.invert_yaxis()

    ax = axes[0, 1]
    dfx = df.pivot(index="server_mtu", columns="peer_mtu", values="upload_send_mbps")
    sns.heatmap(
        dfx.values,
        linewidth=0.5,
        ax=ax,
        cmap="Greens_r",
        xticklabels=list(dfx.columns),
        yticklabels=list(dfx.index),
    )
    ax.tick_params(axis="x", rotation=45)
    ax.tick_params(axis="y", rotation=0)
    ax.set(ylabel="Server MTU", xlabel="Peer MTU")
    ax.set_title("Upload Send Bandwidth (Mbps)")
    ax.invert_yaxis()

    ax = axes[1, 0]
    dfx = df.pivot(index="server_mtu", columns="peer_mtu", values="download_rcv_mbps")
    sns.heatmap(
        dfx.values,
        linewidth=0.5,
        ax=ax,
        cmap="Greens_r",
        xticklabels=list(dfx.columns),
        yticklabels=list(dfx.index),
    )
    ax.tick_params(axis="x", rotation=45)
    ax.tick_params(axis="y", rotation=0)
    ax.set(ylabel="Server MTU", xlabel="Peer MTU")
    ax.set_title("Download Rcv Bandwidth (Mbps)")
    ax.invert_yaxis()

    ax = axes[1, 1]
    dfx = df.pivot(index="server_mtu", columns="peer_mtu", values="download_send_mbps")
    sns.heatmap(
        dfx.values,
        linewidth=0.5,
        ax=ax,
        cmap="Greens_r",
        xticklabels=list(dfx.columns),
        yticklabels=list(dfx.index),
    )
    ax.tick_params(axis="x", rotation=45)
    ax.tick_params(axis="y", rotation=0)
    ax.set(ylabel="Server MTU", xlabel="Peer MTU")
    ax.set_title("Download Send Bandwidth (Mbps)")
    ax.invert_yaxis()

    f.suptitle("Peer MTU vs Server MTU Bandwidth (Mbps)")
    f.tight_layout()
    f.savefig(heatmap_filepath, dpi=300)

    print(
        f"create_heatmap_from_log: Done generating heatmap from log file. Heatmap "
        f"can be found at '{heatmap_filepath}'"
    )
