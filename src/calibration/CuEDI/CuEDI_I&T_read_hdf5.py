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
def show(name, obj):
    print(name, type(obj))

signals = {}
with h5py.File(FILEPATH,"r") as f:
    f.visititems(show)
    signals['Plugins/S12_CuEDI'] = f['Plugins/S12_CuEDI'][:,1]
    # signals['Plugins/SFID'] = f['Plugins/SFID'][:, 1]

print(signals)

fig, ax  = plt.subplots()
dat = signals['Plugins/S12_CuEDI']
ax.scatter([i for i in range(len(dat))],dat,s=10)
ax.set_xlim(195060,195190)
plt.show()
