"""
Plot S14_SCM_X, S15_SCM_Y, S16_SCM_Z against time from the SCM handshake CSV.

Usage:
    python plot_scm_xyz.py [path_to_csv]

If no path is given, it defaults to the filename below.
"""

import sys
import pandas as pd
import matplotlib.pyplot as plt

# ---- Config ----
DEFAULT_PATH = "C:/Users/cfelt/Downloads/52012_SCM_Handshake_8-14-26.csv"
TIME_COL = "Time [-]"
X_COL = "S14_SCM_X [-]"
Y_COL = "S15_SCM_Y [-]"
Z_COL = "S16_SCM_Z [-]"


def load_data(path):
    df = pd.read_csv(path)

    # Time column looks like "226 21:23:12.89864" -> "<day-of-year> HH:MM:SS.ffffff"
    # Split into day-of-year and time-of-day, then build an elapsed-seconds axis.
    time_parts = df[TIME_COL].str.split(" ", n=1, expand=True)
    doy = time_parts[0].astype(int)
    tod = pd.to_timedelta(time_parts[1])

    # Combine day-of-year offset (relative to the first sample's day) with time-of-day
    day_offset = pd.to_timedelta(doy - doy.iloc[0], unit="D")
    elapsed = (day_offset + tod - (day_offset.iloc[0] + tod.iloc[0])).dt.total_seconds()
    df["elapsed_s"] = elapsed

    # Keep only rows where at least one of X/Y/Z has data, since the log
    # interleaves many other signals and most rows are blank for X/Y/Z.
    xyz = df[["elapsed_s", X_COL, Y_COL, Z_COL]].dropna(
        subset=[X_COL, Y_COL, Z_COL], how="all"
    )
    return xyz


def plot_xyz(xyz):
    fig, axes = plt.subplots(3, 1, figsize=(12, 9), sharex=True)

    axes[0].plot(xyz["elapsed_s"], xyz[X_COL], color="tab:red", marker=".", markersize=2, linestyle="none")
    axes[0].set_ylabel("SCM X")

    axes[1].plot(xyz["elapsed_s"], xyz[Y_COL], color="tab:green", marker=".", markersize=2, linestyle="none")
    axes[1].set_ylabel("SCM Y")

    axes[2].plot(xyz["elapsed_s"], xyz[Z_COL], color="tab:blue", marker=".", markersize=2, linestyle="none")
    axes[2].set_ylabel("SCM Z")
    axes[2].set_xlabel("Elapsed time (s)")

    for ax in axes:
        ax.grid(True, alpha=0.3)

    fig.suptitle("SCM X / Y / Z vs Time")
    fig.tight_layout()
    return fig


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PATH
    xyz = load_data(path)
    print(f"Loaded {len(xyz)} rows with at least one non-null X/Y/Z value.")

    fig = plot_xyz(xyz)
    out_png = "scm_xyz_vs_time.png"
    fig.savefig(out_png, dpi=150)
    print(f"Saved plot to {out_png}")

    plt.show()


if __name__ == "__main__":
    main()