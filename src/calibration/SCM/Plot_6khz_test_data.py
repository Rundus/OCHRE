import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
import re
import numpy as np
import pandas as pd

##################################
# --- LOAD THE SIMULATION DATA ---
##################################
# Path to LTspice exported txt file
file_path = "/home/connor/Data/ROCKETS/OCHRE/calibration/SCM/SCM_test_data_post_6khz_knee/rev_OCHRE_LTSpice_sim.txt"

# Regex to extract magnitude and phase
pattern = re.compile(r"\(([^d]+)dB,([^)°]+)")
data = []
with open(file_path, "r",encoding="cp1252") as f:
    lines = f.readlines()

    # Skip header
    for line in lines[1:]:
        line = line.strip()

        if not line:
            continue

        parts = line.split("\t")

        if len(parts) < 2:
            continue

        try:
            freq = float(parts[0])

            match = pattern.search(parts[1])
            if match:
                magnitude_db = float(match.group(1))
                phase_deg = float(match.group(2))

                data.append({
                    "frequency_Hz": freq,
                    "magnitude_dB": magnitude_db,
                    "phase_deg": phase_deg
                })

        except ValueError:
            continue

# Convert to DataFrame
simfreq = [thing['frequency_Hz'] for thing in data]
simGain = [thing['magnitude_dB'] for thing in data]

###########################
# --- LOAD THE LAB DATA ---
###########################
# Directory containing CSV files
# data_dir = r"/home/connor/Data/ROCKETS/OCHRE/calibration/SCM/SCM_test_data_post_6khz_knee"
data_dir = r"/home/connor/Data/ROCKETS/OCHRE/calibration/SCM/SCM_test_data_cal1_linear_output"

# Find all CSV files matching *_sgain.csv
csv_files = glob.glob(os.path.join(data_dir, "*_sgain.csv"))

if not csv_files:
    print("No matching files found.")
    exit()

width = 20
height = 15
Label_Fontsize = 25

plt.figure(figsize=(width, height))

# Plot the simulation data
factor = 7
plt.plot(simfreq, np.array(simGain)-factor,linestyle='--',color='black',label=f'Simulated Gain (- {factor})')

# Plot the test data
for file in csv_files:
    try:
        # Read CSV
        df = pd.read_csv(file)

        filename = os.path.basename(file)
        if "Bx" in filename:
            axis_label = "Bx"
        elif "By" in filename:
            axis_label = "By"
        elif "Bz" in filename:
            axis_label = "Bz"
        else:
            axis_label = "Unknown"

        # Use first two columns
        frequency = df.iloc[:, 0]
        gain = df.iloc[:, 1]

        # Plot
        plt.plot(
            frequency,
            gain,
            label=axis_label
        )

    except Exception as e:
        print(f"Error reading {file}: {e}")

plt.xlabel("Frequency [Hz]", fontsize=Label_Fontsize)
plt.ylabel("Gain [dB]", fontsize=Label_Fontsize)
plt.title("Gain vs Frequency", fontsize=Label_Fontsize)
plt.tick_params(axis='both',labelsize=Label_Fontsize)
plt.grid(True)
plt.xscale('log')
# plt.ylim(-60,1)
plt.legend(fontsize=Label_Fontsize)
plt.tight_layout()




plt.show()