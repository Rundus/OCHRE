# --- energy_Sweep_table_calculation ---
import matplotlib.pyplot as plt
import numpy as np
from src.calibration.CuEDI.sweep_table_determination.sweep_table_toggles import sweepToggles

#################
# --- TOGGLES ---
#################

use_TRACERS_bool = False


#################################
# --- CALCULATE A SWEEP TABLE ---
#################################
# Based on a Maximum Energy and detector resolution, calculate the energies and voltages needed
# for the sweep

if use_TRACERS_bool:
    sweep_steps, sweep_DAC_codes, sweep_voltages, sweep_energies, sweep_errors = sweepToggles().construct_sweep_table()
else:
    sweep_steps,sweep_DAC_codes,sweep_voltages,sweep_energies,sweep_errors = sweepToggles().construct_sweep_table(show_sweep_values=True)

#########################
# --- PLOT EVERYTHING ---
#########################
# sweepToggles().plot_sweep(
#     voltages=sweep_voltages,
#     energies=sweep_energies,
#     errors=sweep_errors,
#     DAC_codes=sweep_DAC_codes,
#     steps=sweep_steps,
# )