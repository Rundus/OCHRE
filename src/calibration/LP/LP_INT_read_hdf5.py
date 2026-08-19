import h5py
import matplotlib.pyplot as plt
import numpy as np

# ----------------------------
# 0. Set your file path here
# ----------------------------
FILEPATH = "C:/Users/cfelt/Downloads/52012_CuEDI_Handshake_8-14-26.hdf"

# ----------------------------
# 1. Pick which signals to plot
# ----------------------------
# Top row: overlay of these signals
TOP_ROW_NAMES = ["OCHRE_LP_allwords"]

# Bottom row: SFID
BOTTOM_ROW_NAMES = ["SFID"]

ALL_NAMES = TOP_ROW_NAMES + BOTTOM_ROW_NAMES

# ----------------------------
# 2. X-axis limits (seconds)
# ----------------------------
XLIM = (6.0, 6.1)

# ----------------------------
# 3. Extract the data
# ----------------------------
signals = {}
with h5py.File(FILEPATH, "r") as f:
    print(ALL_NAMES)
    for name in ALL_NAMES:
        data_path = f"{name}_Data"
        time_path = f"{name}_Time_100nS"

        data = np.asarray(f[data_path][()]).squeeze()
        time_raw = np.asarray(f[time_path][()]).squeeze()

        # Time is stored in units of 100 ns -> convert to seconds
        time_s = time_raw * 100e-9

        # Zero the time axis relative to this signal's first sample
        time_s = time_s - time_s.min()

        print(f"'{name}' time range (zeroed): {time_s.min():.6f} s to {time_s.max():.6f} s "
              f"({time_s.size} points)")

        signals[name] = (time_s, data)

# ----------------------------
# 4. Plot as 2-row subplot
# ----------------------------
fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(9, 7), sharex=True)

# Top row: overlay all signals as scatter with a legend
for name in TOP_ROW_NAMES:
    time_s, data = signals[name]
    axes[0].scatter(time_s, data, s=4, label=name)

axes[0].set_ylabel("Value")
axes[0].set_ylim(-1000,65535)
# axes[0].set_xlim(XLIM)
axes[0].grid(True, alpha=0.3)
axes[0].legend()

# Bottom row: SFID
for name in BOTTOM_ROW_NAMES:
    time_s, data = signals[name]
    axes[1].scatter(time_s, data, s=20, label=name)

axes[1].set_ylabel("SFID")
# axes[1].set_xlim(XLIM)
axes[1].grid(True, alpha=0.3)
axes[1].legend()

axes[-1].set_xlabel("Time (s)")
fig.suptitle("LP Signals and SFID vs Time")
fig.tight_layout()
fig.savefig("deltaN_SFID_plot.png", dpi=150)
plt.show()
