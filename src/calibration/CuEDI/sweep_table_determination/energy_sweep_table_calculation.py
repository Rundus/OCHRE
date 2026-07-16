import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from tabulate import tabulate
import spaceToolsLib as stl


class SweepTable:

    # --- Instrument parameters ---
    DeltaE = 0.18  # in decimal percent. This is the FWHM value
    Delta_r = 0.055  # [Inches] inner radius spacing between hemispheres
    rout = 0.945  # [Inches] the diameter of the outer hemisphere

    # --- Emax ---
    Emax = 11000  # in [eV]
    N_steps = 49
    step_numbers = np.array([i + 1 for i in range(N_steps)])
    DAC_bitDepth = 12
    DAC_Vref = 3.6  # in Volts
    feedback_gain_ratio = 500  # 500:1 for OCHRE, 1000:1 for ACES-II

    # --- DAC-code sweep parameters (for construct_sweep_table_from_DAC_codes) ---
    N_linear_DAC = 0  # number of steps, at the low-DAC-code end, generated linearly rather than exponentially
    DAC_start = 3379  # highest DAC code in the sweep (upper bound)
    DAC_stop = 2  # lowest DAC code in the sweep (lower bound)


    # ------------------------------------------------------------------
    # DAC-code-based sweep construction
    # ------------------------------------------------------------------
    def construct_sweep_table_from_DAC_codes(self, **kwargs):
        """
        Construct a descending sweep of N_steps DAC codes between DAC_start (high)
        and DAC_stop (low). The upper (N_steps - N_linear_DAC) steps are spaced
        exponentially/geometrically; the lower N_linear_DAC steps are spaced linearly
        down to DAC_stop.
        """
        code_max = 2 ** self.DAC_bitDepth - 1
        code_min = 0

        # --- validation ---
        if not (code_min <= self.DAC_stop < self.DAC_start <= code_max):
            raise ValueError(
                f"DAC_start ({self.DAC_start}) and DAC_stop ({self.DAC_stop}) must satisfy "
                f"{code_min} <= DAC_stop < DAC_start <= {code_max}"
            )


        if not (0 <= self.N_linear_DAC <= self.N_steps):
            raise ValueError("N_linear_DAC must be between 0 and N_steps")

        N_exp = self.N_steps - self.N_linear_DAC

        if self.N_linear_DAC == 0:
            # entire sweep is exponential
            sweep_DAC_codes = np.geomspace(self.DAC_start, self.DAC_stop, self.N_steps)
        elif N_exp == 0:
            # entire sweep is linear
            sweep_DAC_codes = np.linspace(self.DAC_start, self.DAC_stop, self.N_steps)
        else:
            # find the transition code that splits the sweep into N_exp exponential
            # steps followed by N_linear_DAC linear steps
            transition_code = np.geomspace(self.DAC_start, self.DAC_stop, N_exp + 1)[-1]
            exp_codes = np.geomspace(self.DAC_start, transition_code, N_exp, endpoint=False)
            linear_codes = np.linspace(transition_code, self.DAC_stop, self.N_linear_DAC)
            sweep_DAC_codes = np.concatenate([exp_codes, linear_codes])

        sweep_DAC_codes = np.round(sweep_DAC_codes).astype(int)
        sweep_steps = self.step_numbers

        # --- invert digitize() to recover hemisphere voltages ---
        DAC_per_volt = (code_max - code_min) / (self.DAC_Vref - 0)
        sweep_voltages = (sweep_DAC_codes / DAC_per_volt) * self.feedback_gain_ratio

        # --- invert Vset() to recover energies ---
        sweep_energies = sweep_voltages * (self.rout / self.Delta_r + 3 / 2) / 2

        # --- errors, same convention as construct_sweep_table_from_Emax ---
        energy_err_neg = sweep_energies * (self.DeltaE / 2)
        energy_err_pos = sweep_energies * (self.DeltaE / 2)
        sweep_errors = np.array([energy_err_neg, energy_err_pos])

        if kwargs.get('show_sweep_values', False):
            rows = list(zip(sweep_steps, sweep_DAC_codes, sweep_voltages, sweep_energies))
            print(
                tabulate(rows, headers=["Step No.", "DAC Code", "Hemisphere Volt [V]", "Energy [eV]"], floatfmt=".6f"))

        return sweep_steps, sweep_DAC_codes, sweep_voltages, sweep_energies, sweep_errors

    def construct_sweep_table_from_Emax(self):
        sweep_energies = []

        previous = self.Emax
        for i in range(self.N_steps):
            engy = previous
            if i != 0:
                new_engy = engy * ((1 - self.DeltaE / 2) / (1 + self.DeltaE / 2))
                sweep_energies.append(new_engy)
                previous = new_engy
            else:
                sweep_energies.append(engy)

        # ENERGIES
        sweep_energies = np.array(sweep_energies)
        energy_err_neg = sweep_energies * (self.DeltaE / 2)
        energy_err_pos = sweep_energies * (self.DeltaE / 2)
        sweep_errors = np.array([energy_err_neg, energy_err_pos])

        # VOLTAGES
        sweep_voltages = self.Vset(sweep_energies)

        # DAC Value
        sweep_DAC_codes = np.round(self.digitize(sweep_voltages / self.feedback_gain_ratio))
        sweep_steps = self.step_numbers


        return sweep_steps, sweep_DAC_codes, sweep_voltages, sweep_energies, sweep_errors

    def construct_TRACERS_sweep_table(self):
        sweep_steps = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
                       21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38,
                       39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 49, 50]
        sweep_DAC_codes = [3379, 2952, 2578, 2252, 1968, 1719, 1501, 1312, 1146, 1001, 874, 764, 667,
                           583, 509, 445, 388, 339, 296, 259, 226, 198, 173, 151, 132, 115, 101, 88,
                           77, 67, 59, 51, 45, 39, 34, 30, 26, 23, 20, 17, 15, 13, 12, 10, 9, 8, 7,
                           6, 6, 1690]
        sweep_low_voltages = [2.970549451, 2.595164835, 2.266373626, 1.97978022, 1.73010989,
                              1.511208791, 1.31956044, 1.153406593, 1.007472527, 0.88,
                              0.768351648, 0.671648352, 0.586373626, 0.512527473, 0.447472527,
                              0.391208791, 0.341098901, 0.298021978, 0.26021978, 0.227692308,
                              0.198681319, 0.174065934, 0.152087912, 0.132747253, 0.116043956,
                              0.101098901, 0.088791209, 0.077362637, 0.067692308, 0.058901099,
                              0.051868132, 0.044835165, 0.03956044, 0.034285714, 0.02989011,
                              0.026373626, 0.022857143, 0.02021978, 0.017582418, 0.014945055,
                              0.013186813, 0.011428571, 0.010549451, 0.008791209, 0.007912088,
                              0.007032967, 0.006153846, 0.005274725, 0.005274725, 1.485714286]
        sweep_voltages = [1485.274725, 1297.582418, 1133.186813, 989.8901099, 865.0549451,
                          755.6043956, 659.7802198, 576.7032967, 503.7362637, 440,
                          384.1758242, 335.8241758, 293.1868132, 256.2637363, 223.7362637,
                          195.6043956, 170.5494505, 149.010989, 130.1098901, 113.8461538,
                          99.34065934, 87.03296703, 76.04395604, 66.37362637, 58.02197802,
                          50.54945055, 44.3956044, 38.68131868, 33.84615385, 29.45054945,
                          25.93406593, 22.41758242, 19.78021978, 17.14285714, 14.94505495,
                          13.18681319, 11.42857143, 10.10989011, 8.791208791, 7.472527473,
                          6.593406593, 5.714285714, 5.274725275, 4.395604396, 3.956043956,
                          3.516483516, 3.076923077, 2.637362637, 2.637362637, 742.8571429]
        sweep_energies = [11041, 9843.5, 8773.2, 7818.3, 6970.8,
                          6210.9, 5538.5, 4933.7, 4400.5, 3923.1,
                          3493.4, 3115.4, 2777.2, 2474.8, 2204.2,
                          1965.5, 1754.6, 1563.7, 1392.6, 1241.4,
                          1106.1, 986.74, 879.31, 783.82, 700.27,
                          620.69, 553.05, 493.37, 441.65, 393.9,
                          350.13, 310.35, 278.52, 246.68, 222.81,
                          198.94, 175.07, 155.17, 139.26, 123.34,
                          111.41, 99.47, 87.533, 79.576, 71.618,
                          63.661, 55.703, 47.745, 43.767, None]

        DeltaE_TRACERS = 0.18
        sweep_energies = np.array(sweep_energies)
        energy_err_neg = sweep_energies * (DeltaE_TRACERS / 2)
        energy_err_pos = sweep_energies * (DeltaE_TRACERS / 2)
        sweep_errors = np.array([energy_err_neg, energy_err_pos])

        return sweep_steps, sweep_DAC_codes, sweep_voltages, sweep_energies, sweep_errors

    def construct_sweep_table(self, **kwargs):

        plot_bool = kwargs.get('plot_sweep', False)
        print_bool = kwargs.get('print_sweep',False)
        sweep_type = kwargs.get('type', [])  # Valid Values ['TRACERS','DAC','Emax']

        if sweep_type == 'TRACERS':
            table = self.construct_TRACERS_sweep_table()
        elif sweep_type=='DAC':
            table = self.construct_sweep_table_from_DAC_codes()
        elif sweep_type=='Emax':
            table = self.construct_sweep_table_from_Emax()
        else:
            raise ValueError("Invalid Sweep Type")

        if plot_bool:
            self.plot_sweep(*table,sweep_type)

        if print_bool:
            rows = list(zip(table[0], table[1], table[2], table[3]))
            print(tabulate(rows, headers=["Step No.", "DAC Code (x2 cal)", "Hemisphere Volt [V]", "Energy [eV]"],floatfmt=".6f"))

        return table

    # Define the energy permitted into the detector based on the input voltage
    def Epermitted(self, Vset, charge):
        """
        :param Vset:
        :param charge:
        :return:
            permitted energy in Joules
        """
        return (-1 * charge * Vset / 2) * (self.rout / self.Delta_r + 3 / 2)

    def Vset(self, Epermitted):
        """
        :param Epermitted: Input Energy, IN EV (already accounted for J-> eV Conversion)
        :return:
            Voltage in [V]
        """
        return (2 * Epermitted) / (self.rout / self.Delta_r + 3 / 2)

    def digitize(self, Voltage):
        code_max = 2 ** (self.DAC_bitDepth) - 1
        code_min = 0
        DAC_per_volt = ((code_max - code_min) / (self.DAC_Vref - 0))
        return Voltage * DAC_per_volt

    def plot_sweep(self, sweep_steps, sweep_DAC_codes, sweep_voltages, sweep_energies, sweep_errors,type_name):

        # plot everything
        fig, ax = plt.subplots(3, sharex=True)
        fig.suptitle(f'{type_name} Sweep')

        # Energies
        ax[0].scatter(sweep_steps, sweep_energies)
        ax[0].errorbar(sweep_steps, sweep_energies, yerr=sweep_errors, capsize=5)
        ax[0].set_ylabel('Energy (Estimate) [eV]')
        # ax[0].set_ylim(0,14000)

        # Voltages
        ax[1].scatter(sweep_steps, sweep_voltages)
        ax[1].set_ylabel('Inner Hemisphere Voltage [V]')
        # ax[1].set_ylim(0,1400)

        # DAC Value
        ax[2].scatter(sweep_steps, sweep_DAC_codes)
        ax[2].set_ylabel('DAC Code')
        # ax[2].set_ylim(0, 1400)

        # Adjustments
        for i in range(3):
            ax[i].grid()
            ax[i].set_xticks([i + 1 for i in range(len(sweep_steps))])
            # ax.set_yscale('log')
            if i == 2:
                ax[i].set_xlabel('Step Number')
        plt.show()


#################################
# --- CALCULATE A SWEEP TABLE ---
#################################
# Based on a Maximum Energy and detector resolution, calculate the energies and voltages needed
# for the sweep

sweep_steps, sweep_DAC_codes, sweep_voltages, sweep_energies, sweep_errors = SweepTable().construct_sweep_table(type='DAC',
                                                                                                                plot_sweep=False,
                                                                                                                print_sweep=True)