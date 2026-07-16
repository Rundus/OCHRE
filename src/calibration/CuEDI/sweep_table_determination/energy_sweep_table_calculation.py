"""
sweep_table.py

Builds hemisphere-analyzer sweep tables (step number -> DAC code -> hemisphere
voltage -> pass energy) for an electrostatic analyzer instrument.

A "sweep table" can be constructed three ways:
    - 'Emax'    : derive DAC codes/voltages from a target max energy and the
                  instrument's energy resolution (DeltaE).
    - 'DAC'     : derive voltages/energies by starting from a specified range
                  of DAC codes (partially exponential, partially linear).
    - 'TRACERS' : a fixed, hardcoded sweep table used for the TRACERS mission.

Use SweepTable().construct_sweep_table(type=..., plot_sweep=..., print_sweep=...)
as the single entry point; it dispatches to the appropriate constructor below.
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from tabulate import tabulate
import spaceToolsLib as stl


class SweepTable:
    """
    Computes and (optionally) plots/prints the energy sweep table for an
    electrostatic hemispherical analyzer.

    The instrument sweeps the inner hemisphere voltage across N_steps values.
    Each step corresponds to:
        - a DAC code (12-bit, 0 to 2^DAC_bitDepth - 1) sent to the high-voltage
          supply,
        - a hemisphere voltage (DAC code scaled by DAC_Vref and the feedback
          gain ratio of the HV supply),
        - a pass/permitted energy (a function of hemisphere voltage and the
          analyzer's geometric constants Delta_r and rout).

    Class attributes
    ----------------
    DeltaE : float
        Fractional (FWHM) energy resolution of the analyzer, e.g. 0.18 = 18%.
        Used both to step the energy sweep geometrically (construct_sweep_table_from_Emax)
        and to report +/- energy uncertainty on every sweep table.
    Delta_r : float
        Inner-to-outer hemisphere radius spacing, in inches.
    rout : float
        Outer hemisphere radius (diameter, per original comment), in inches.
    Emax : float
        Target maximum pass energy, in eV, used as the starting point for the
        'Emax'-based sweep.
    N_steps : int
        Number of steps in the sweep (table length).
    step_numbers : np.ndarray
        1-indexed array [1, 2, ..., N_steps] used as the step-number axis for
        all sweep tables.
    DAC_bitDepth : int
        Bit depth of the DAC driving the HV supply (defines valid code range
        0 to 2**DAC_bitDepth - 1).
    DAC_Vref : float
        DAC reference voltage, in Volts.
    feedback_gain_ratio : float
        Gain ratio of the HV supply's feedback network (DAC output volts :
        actual hemisphere volts), e.g. 500 for OCHRE, 1000 for ACES-II.
    N_linear_DAC : int
        Number of steps, at the low-DAC-code (bottom) end of the DAC-code
        sweep, that are spaced linearly rather than exponentially. The
        remaining (N_steps - N_linear_DAC) steps at the high-code end are
        spaced geometrically. Used only by construct_sweep_table_from_DAC_codes.
    DAC_start : int
        Highest DAC code in the DAC-code sweep (upper bound, first step).
    DAC_stop : int
        Lowest DAC code in the DAC-code sweep (lower bound, last step).
    """

    # --- Instrument parameters ---
    DeltaE = 0.18  # in decimal percent. This is the FWHM value
    Delta_r = 0.055  # [Inches] inner radius spacing between hemispheres
    rout = 0.945  # [Inches] the diameter of the outer hemisphere

    # --- Emax Sweep Toggles---
    Emax = 11000  # in [eV]
    N_steps = 49
    step_numbers = np.array([i + 1 for i in range(N_steps)])
    DAC_bitDepth = 12
    DAC_Vref = 3.6  # in Volts
    feedback_gain_ratio = 500  # 500:1 for OCHRE, 1000:1 for ACES-II

    # --- DAC-code sweep parameters (for construct_sweep_table_from_DAC_codes) ---
    N_linear_DAC = 0  # number of steps, at the low-DAC-code end, generated linearly rather than exponentially
    DAC_start = 3000  # highest DAC code in the sweep (upper bound)
    DAC_stop = 2  # lowest DAC code in the sweep (lower bound)
    DAC_transition =10  # DAC code marking the upper limit of the linear region / boundary between the exponential and linear portions

    # ------------------------------------------------------------------
    # DAC-code-based sweep construction
    # ------------------------------------------------------------------
    def construct_sweep_table_from_DAC_codes(self, **kwargs):
        """
        Construct a descending sweep of N_steps DAC codes between DAC_start
        (high) and DAC_stop (low), then back-calculate the corresponding
        hemisphere voltages and pass energies.

        The upper (N_steps - N_linear_DAC) steps are spaced exponentially
        (geometrically) from DAC_start down to an intermediate transition
        code; the lower N_linear_DAC steps are spaced linearly from that
        transition code down to DAC_stop. Setting N_linear_DAC = 0 makes the
        whole sweep exponential; setting N_linear_DAC = N_steps makes the
        whole sweep linear.

        Voltages are recovered by inverting digitize(): DAC_code -> Volts,
        then rescaling by feedback_gain_ratio to get the actual hemisphere
        voltage (undoing the gain division applied when a voltage is
        converted to a DAC code elsewhere in this class).

        Energies are recovered by inverting Vset(): Volts -> eV.

        Parameters
        ----------
        **kwargs :
            show_sweep_values : bool, optional (default False)
                If True, print a formatted table of step number, DAC code,
                hemisphere voltage, and energy.

        Returns
        -------
        sweep_steps : np.ndarray
            1-indexed step numbers, length N_steps.
        sweep_DAC_codes : np.ndarray of int
            DAC codes for each step, descending from DAC_start to DAC_stop.
        sweep_voltages : np.ndarray
            Hemisphere voltage [V] for each step.
        sweep_energies : np.ndarray
            Pass energy [eV] for each step.
        sweep_errors : np.ndarray, shape (2, N_steps)
            [negative_error, positive_error] on energy, each equal to
            energy * (DeltaE / 2), matching the convention used elsewhere
            in this class.

        Raises
        ------
        ValueError
            If DAC_start/DAC_stop fall outside the valid DAC code range or
            DAC_start <= DAC_stop, or if N_linear_DAC is outside [0, N_steps].
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

        if not (self.DAC_stop <= self.DAC_transition <= self.DAC_start):
            raise ValueError(
                f"DAC_transition ({self.DAC_transition}) must satisfy "
                f"DAC_stop ({self.DAC_stop}) <= DAC_transition <= DAC_start ({self.DAC_start})"
            )

        if self.N_linear_DAC == 0:
            # entire sweep is exponential
            sweep_DAC_codes = np.geomspace(self.DAC_start, self.DAC_stop, self.N_steps)
        elif N_exp == 0:
            # entire sweep is linear
            sweep_DAC_codes = np.linspace(self.DAC_start, self.DAC_stop, self.N_steps)
        else:
            # transition_code is the explicitly-specified upper bound of the linear
            # region (DAC_transition), splitting the sweep into N_exp exponential
            # steps followed by N_linear_DAC linear steps
            transition_code = self.DAC_transition
            exp_codes = np.geomspace(self.DAC_start, transition_code, N_exp, endpoint=False)
            linear_codes = np.linspace(transition_code, self.DAC_stop, self.N_linear_DAC)
            sweep_DAC_codes = np.concatenate([exp_codes, linear_codes])

        sweep_DAC_codes = np.round(sweep_DAC_codes).astype(int)
        sweep_steps = self.step_numbers

        # --- invert digitize() to recover hemisphere voltages ---
        DAC_per_volt = (code_max - code_min) / (self.DAC_Vref - 0)
        sweep_voltages = (sweep_DAC_codes / DAC_per_volt) * self.feedback_gain_ratio

        # --- invert Vset() to recover energies ---
        # sweep_energies = sweep_voltages * (self.rout / self.Delta_r + 3 / 2) / 2
        sweep_energies = sweep_voltages * (self.rout / self.Delta_r ) / 2

        # --- errors, same convention as construct_sweep_table_from_Emax ---
        energy_err_neg = sweep_energies * (self.DeltaE / 2)
        energy_err_pos = sweep_energies * (self.DeltaE / 2)
        sweep_errors = np.array([energy_err_neg, energy_err_pos])


        return sweep_steps, sweep_DAC_codes, sweep_voltages, sweep_energies, sweep_errors

    def construct_sweep_table_from_Energy(self):
        """
        Construct a sweep table by stepping down geometrically from Emax.

        Starting at Emax, each subsequent step's energy is scaled by
        (1 - DeltaE/2) / (1 + DeltaE/2), which produces steps spaced so that
        adjacent energy windows (each energy +/- DeltaE/2 of itself) just
        touch -- i.e. a resolution-matched geometric energy sweep with
        N_steps points.

        DAC codes and voltages are then derived forward from these energies
        via Vset() and digitize().

        Returns
        -------
        sweep_steps : np.ndarray
            1-indexed step numbers, length N_steps.
        sweep_DAC_codes : np.ndarray
            DAC codes for each step (rounded, not cast to int).
        sweep_voltages : np.ndarray
            Hemisphere voltage [V] for each step.
        sweep_energies : np.ndarray
            Pass energy [eV] for each step, geometrically descending from Emax.
        sweep_errors : np.ndarray, shape (2, N_steps)
            [negative_error, positive_error] on energy, each equal to
            energy * (DeltaE / 2).
        """
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
        """
        Return the fixed, hardcoded 50-point sweep table used for the
        TRACERS mission (not derived from Emax or DAC_start/DAC_stop).

        Note the final energy value is None (no corresponding measured/
        calculated energy for that step) and sweep_steps/sweep_DAC_codes
        etc. are length 50, one longer than N_steps (49), since this table
        is independent of the class's general N_steps parameter.

        Returns
        -------
        sweep_steps : list of int
            Step numbers (length 50; note step 49 appears twice in the
            source data).
        sweep_DAC_codes : list of int
            DAC codes for each step.
        sweep_voltages : list of float
            Hemisphere voltage [V] for each step.
        sweep_energies : np.ndarray
            Pass energy [eV] for each step; last element is None.
        sweep_errors : np.ndarray, shape (2, 50)
            [negative_error, positive_error] on energy, each equal to
            energy * (DeltaE_TRACERS / 2). Note: since the last energy is
            None, the last error entries will be None/NaN-like as well.
        """
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
        """
        Single entry point for building a sweep table. Dispatches to one of
        the three constructors below based on `type`, and optionally plots
        and/or prints the result.

        Parameters
        ----------
        **kwargs :
            type : str
                Which sweep to build. One of 'TRACERS', 'DAC', 'Emax'.
                Required; raises ValueError if missing or invalid.
            plot_sweep : bool, optional (default False)
                If True, call plot_sweep() on the resulting table.
            print_sweep : bool, optional (default False)
                If True, print a formatted table of step number, DAC code,
                voltage, and energy.

        Returns
        -------
        table : tuple
            (sweep_steps, sweep_DAC_codes, sweep_voltages, sweep_energies,
            sweep_errors) as returned by the selected constructor.

        Raises
        ------
        ValueError
            If `type` is not one of 'TRACERS', 'DAC', 'Emax'.
        """

        plot_bool = kwargs.get('plot_sweep', False)
        print_bool = kwargs.get('print_sweep', False)
        sweep_type = kwargs.get('type', [])  # Valid Values ['TRACERS','DAC','Emax']
        csv_path = kwargs.get('to_csv', None)

        if sweep_type == 'TRACERS':
            table = self.construct_TRACERS_sweep_table()
        elif sweep_type == 'DAC':
            table = self.construct_sweep_table_from_DAC_codes()
        elif sweep_type == 'Emax':
            table = self.construct_sweep_table_from_Emax()
        else:
            raise ValueError("Invalid Sweep Type")

        if plot_bool:
            self.plot_sweep(*table, sweep_type)

        if print_bool:
            diffs = -1*np.diff(table[3])
            denomenator = (table[3][0:-1] + table[3][1:])/2
            resolution =  diffs/ denomenator
            resolution += [resolution[-1]]
            rows = list(zip(table[0], table[1], table[2], table[3],resolution))
            print(tabulate(rows, headers=["Step No.", "DAC Code (x2 cal)", "Hemisphere Volt [V]", "Energy [eV]",'Resolution'], floatfmt=".3f"))

        if csv_path:
            sweep_steps, sweep_DAC_codes, sweep_voltages, sweep_energies, sweep_errors = table
            df = pd.DataFrame({
                "Step No.": sweep_steps,
                "DAC Code": sweep_DAC_codes,
                "Hemisphere Volt [V]": sweep_voltages,
                "Energy [eV]": sweep_energies,
                "Energy Err Neg [eV]": sweep_errors[0],
                "Energy Err Pos [eV]": sweep_errors[1],
            })
            df.to_csv(csv_path, index=False)

        return table

    def Epermitted(self, Vset, charge):
        """
        Compute the pass ("permitted") energy admitted into the detector for
        a given hemisphere voltage and particle charge.

        This is the forward physical relation (voltage/charge -> energy in
        Joules); note it is the inverse direction and different unit
        convention from Vset(), which works in eV.

        Parameters
        ----------
        Vset : float or np.ndarray
            Hemisphere voltage [V].
        charge : float
            Particle charge (e.g. in Coulombs; sign matters -- determines
            the sign of the returned energy).

        Returns
        -------
        float or np.ndarray
            Permitted energy, in Joules.
        """
        # return (-1 * charge * Vset / 2) * (self.rout / self.Delta_r + 3 / 2)

        return (-1 * charge * Vset / 2) * (self.rout / self.Delta_r )

    def Vset(self, Epermitted):
        """
        Compute the hemisphere voltage required to admit a given pass energy.

        Inverse of the eV-based energy/voltage relation used throughout this
        class (i.e. the forward direction used by construct_sweep_table_from_Emax,
        and the relation inverted by construct_sweep_table_from_DAC_codes).

        Parameters
        ----------
        Epermitted : float or np.ndarray
            Desired pass energy, in eV.

        Returns
        -------
        float or np.ndarray
            Required hemisphere voltage, in Volts.
        """
        return (2 * Epermitted) / (self.rout / self.Delta_r + 3 / 2)

    def digitize(self, Voltage):
        """
        Convert a voltage into the corresponding DAC code for this
        instrument's DAC (DAC_bitDepth bits, referenced to DAC_Vref).

        Parameters
        ----------
        Voltage : float or np.ndarray
            Voltage to digitize, in Volts (already scaled to the DAC's
            input range, i.e. hemisphere voltage / feedback_gain_ratio).

        Returns
        -------
        float or np.ndarray
            DAC code (not rounded/cast to int here; callers typically
            apply np.round()).
        """
        code_max = 2 ** (self.DAC_bitDepth) - 1
        code_min = 0
        DAC_per_volt = ((code_max - code_min) / (self.DAC_Vref - 0))
        return Voltage * DAC_per_volt

    def plot_sweep(self, sweep_steps, sweep_DAC_codes, sweep_voltages, sweep_energies, sweep_errors, type_name):
        """
        Plot a sweep table as three stacked scatter plots (energy with error
        bars, hemisphere voltage, DAC code) all sharing a step-number x-axis.

        Parameters
        ----------
        sweep_steps : array-like
            Step numbers (x-axis for all three subplots).
        sweep_DAC_codes : array-like
            DAC code per step (bottom subplot).
        sweep_voltages : array-like
            Hemisphere voltage [V] per step (middle subplot).
        sweep_energies : array-like
            Pass energy [eV] per step (top subplot).
        sweep_errors : array-like, shape (2, N)
            [negative_error, positive_error] on energy, used for error bars
            on the top subplot.
        type_name : str
            Label identifying which sweep type this is (e.g. 'DAC', 'Emax',
            'TRACERS'); used in the figure title.

        Returns
        -------
        None
            Displays the plot via plt.show(); does not return a value.
        """

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

sweep_steps, sweep_DAC_codes, sweep_voltages, sweep_energies, sweep_errors = SweepTable().construct_sweep_table(
    type='DAC',
    plot_sweep=False,
    print_sweep=True,
    to_csv='/home/connor/PycharmProjects/OCHRE/src/calibration/CuEDI/sweep_table_determination/sweep_table.csv')