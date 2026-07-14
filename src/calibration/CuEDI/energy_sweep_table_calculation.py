# --- energy_Sweep_table_calculation ---
import matplotlib.pyplot as plt
import numpy as np

# Instrument parameters
DeltaE = 0.18 # in decimal percent. This is the FWHM value
Delta_r = 0.055 # [Inches] inner radius spacing between hemispheres
rout = 0.945 # [Inches] the diameter of the outer hemisphere

# Sweep parameters
Emax = 12000 # in [eV]
N_steps = 49
step_numbers = np.array([i+1 for i in range(N_steps)])
DAC_bitDepth = 12
DAC_Vref = 2.5 # in Volts

# Define the energy permitted into the detector based on the input voltage
def Epermitted(Vset,charge):
    """
    :param Vset:
    :param charge:
    :return:
        permitted energy in Joules
    """
    return (-1**Vset*charge/2)*(rout/Delta_r + 3/2)

def Vset(Epermitted):
    """
    :param Epermitted: Input Energy, in eV
    :return:
        Voltage
    """
    return 2*Epermitted/(rout/Delta_r + 3/2)

def digitize(Voltage):
    code_max = 2**(DAC_bitDepth)-1
    code_min = 0
    DAC_per_volt = ((code_max - code_min)/(DAC_Vref-0))
    return Voltage*DAC_per_volt



# Based on a Maximum Energy and detector resolution, calculate the energies and voltages needed
# for the sweep

sweep_energies = []
sweep_voltages = []

previous = Emax
for i in range(N_steps):
    engy = previous
    if i != 0:
        new_engy = engy*((1-DeltaE/2)/(1+DeltaE/2))
        sweep_energies.append(new_engy)
        previous = new_engy
    else:
        sweep_energies.append(engy)

# ENERGIES
sweep_energies = np.array(sweep_energies)
energy_err_neg = sweep_energies*(DeltaE/2)
energy_err_pos = sweep_energies*(DeltaE/2)
errors = np.array([energy_err_neg,energy_err_pos])

# VOLTAGES
sweep_voltages = Vset(sweep_energies)

# DAC Value
sweep_DAC_codes = np.round(digitize(sweep_voltages/1000))

# plot everything
fig, ax = plt.subplots(3,sharex=True)

# Energies
ax[0].scatter(step_numbers,sweep_energies)
ax[0].errorbar(step_numbers,sweep_energies,yerr=errors,capsize=5)
ax[0].set_ylabel('Energy [eV]')
# ax[0].set_ylim(0,14000)

# Voltages
ax[1].scatter(step_numbers,sweep_voltages)
ax[1].set_ylabel('Volts [V]')
# ax[1].set_ylim(0,1400)

# DAC Value
ax[2].scatter(step_numbers,sweep_DAC_codes)
ax[2].set_ylabel('DAC Code')
# ax[2].set_ylim(0, 1400)


# Adjustments
for i in range(3):
    ax[i].grid()
    ax[i].set_xticks([i+1 for i in range(N_steps)])
    # ax.set_yscale('log')
    if i == 2:
        ax[i].set_xlabel('Step Number')
plt.show()