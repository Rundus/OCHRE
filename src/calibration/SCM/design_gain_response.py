# --- design_gain_response ---
# Description: Code to see what the gain of the Low Pass Filter
# on the output of the SCM is and change it as needed


# --- imports ---
import matplotlib.pyplot as plt
import numpy as np


# get the frequency space data
freq_space = np.linspace(10, 1E5, 1000)


def transimpedance_amp(freq):
    return

def high_pass_filter(freq):
    C1 = 22E9
    C2 = 22E9
    R1 = 931E3
    R2 = 562E3
    fc = 1/(2*np.pi*np.sqrt(R1*R2*C1*C2))

    # non-inverting op amp
    RA1 = 698E3
    RA2 = 392E3
    Av = 1 + RA1 / RA2
    return np.array([Av for i in range(len(freq))])

A_HP = high_pass_filter(freq_space)

# --- (initial) ---
def low_pass_differential_op_amp_gain(freq): # determine the gain for the passive low-pass filter
    R1 = 20E3
    R2 = 20E3
    R3 = 10E3
    R4 = 10E4
    C1 = 10E-12
    fc = 1/(2*np.pi*R3*C1)
    return (R3/R1)*1/(np.sqrt(1 + np.power(freq/fc,2)))

A_0 = low_pass_differential_op_amp_gain(freq_space)

# --- first stage (passive) ---
def first_stage_gain(freq): # determine the gain for the passive low-pass filter
    R = 11.3E3
    C = 22E-9
    fc = 1/(2*np.pi*R*C)
    return 1/np.sqrt(1 + np.power(freq/fc,2))

A_1 = first_stage_gain(freq_space)

# --- second stage (2nd-order butterworth) ---
def second_stage_gain(freq):

    # butterworth filter
    R1 = 10.7E3
    R2 = 3.16E3
    C1 = 22E-9
    C2 = 22E-9
    fc = 1 / (2 * np.pi * np.sqrt(C1 * C2 * R1 * R2))

    # non-inverting op amp
    RA1 = 698
    RA2 = 1E3
    Av = 1 + RA1 / RA2

    return Av * (1/np.sqrt(1 + np.power(freq/fc,4)))

A_2 = second_stage_gain(freq_space)

# --- third stage (2nd-order butterworth) ---
def third_stage_gain(freq):
    # butterworth filter
    R1 = 7.5E3
    R2 = 10.2E3
    C1 = 15E-9
    C2 = 22E-9
    fc = 1 / (2 * np.pi * np.sqrt(C1 * C2 * R1 * R2))

    # non-inverting op amp
    RA1 = 698
    RA2 = 1E3
    Av = 1 + RA1 / RA2

    return Av * (1 / np.sqrt(1 + np.power(freq / fc, 4)))

A_3 = third_stage_gain(freq_space)

# --- Plot Everything ---
Gains = [A_HP, A_0, A_1, A_2, A_3]
Total =A_HP*A_0*A_1*A_2*A_3
Labels = ['High Pass','Differential Op Amp', 'Passive Low Pass', '2nd Butterworth (1)', '2nd Butterworth (2)']

# plot it all
fig, ax = plt.subplots()
ax.set_xscale('log')
ax.set_xlim(1E1, 1E4)
for idx, gain in enumerate(Gains):
    ax.plot(freq_space, gain, label=f"{Labels[idx]}")

ax.plot(freq_space, Total,label='Total')
ax.axhline(1/np.sqrt(2),linestyle='--')
ax.set_ylabel('Vin/Vout')
ax.set_xlabel('Freq [Hz]')
ax.grid()
ax.legend()
plt.show()