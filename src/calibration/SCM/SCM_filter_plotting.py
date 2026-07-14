import pandas as pd
import matplotlib.pyplot as plt

folder = r'C:\Data\OCHRE\testing\SCM_bench'
file_premod = f'{folder}\\Studetrocket_EM2_SN2_board-premod_TRACERS_HPonly_gainredo_2_20250327_gain.csv'
file_mod = f'{folder}\\Student_Rocket_EM2_SN1_board_aftermod2_X_oldcan_gompa_hp3385only_20250403_gain.csv'
file_LTSpice = ''

dataFrame_premod = pd.DataFrame( pd.read_csv(file_premod))
dataFrame_mod = pd.DataFrame(pd.read_csv(file_mod))
dataFrame_LTSpice = pd.DataFrame(pd.read_excel(f'{folder}\\rev_OCHRE_output_Data.xlsx'))


def dBm_to_dbV(amplitude):
    return (0.224 * (10 **((amplitude) / 20)))

# prepare the data
xData_LTspice = dataFrame_LTSpice.loc[:,'1']
yData_LTspice = dataFrame_LTSpice.loc[:,'-5.20E+01']

xData_premod = dataFrame_premod.loc[:,'Frequency (Hz)']
yData_premod = dataFrame_premod.loc[:,'Amplitude (V)']

xData_mod = dataFrame_mod.loc[:,'Frequency (Hz)']
yData_mod = dataFrame_mod.loc[:,'Amplitude (V)']

# plot the data
fig, ax = plt.subplots()
plt.plot(xData_LTspice,yData_LTspice, color='tab:blue', label='LTspice')
plt.plot(xData_premod,yData_premod, color='tab:red', label='premod')
plt.plot(xData_mod,yData_mod, color='tab:green', label='mod')
ax.legend()
ax.set_ylabel('V [dB]')
ax.set_xscale('log')
ax.set_xlabel('Frequency [Hz]')
ax.set_xlim(1, 1E5)
ax.set_ylim(-50, 10)
plt.show()