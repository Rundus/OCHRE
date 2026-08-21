"""
Decode CuEDI_all_words telemetry from an OCHRE/IEPAA CDF file.

Structure discovered from the data:
  - Minor_frame_idx cycles 0-9, with each value repeated 17 times in a row
    (17 raw CuEDI_allWords samples = 1 "minor frame word block").
  - Two consecutive minor frames (an even value followed by the next odd
    value, e.g. 0+1, 2+3, 4+5 ...) together form a 34-sample cycle.
  - Within that 34-sample cycle:
      physical offset 0        -> "34th word" / 625 kHz clock (mostly 437,
                                   drifts to 438/439, periodically resets to 0)
      physical offset 3        -> "4th word" (16-bit bitfield: HV/16, step
                                   number, HV enable, test pulse enable)
      physical offset 4        -> "5th word" (12-bit field, mask with 0xFFF)
      physical offset 13-33    -> unused / always zero

  Word numbering in this script is 1-indexed to match how the words were
  described verbally (e.g. "4th word" = offset 3 = index 3).

Requires: pip install cdflib numpy
"""

import spaceToolsLib as stl
import numpy as np
from copy import deepcopy
from src.processing.processing_classes import ProcessingClass
import glob
import matplotlib.pyplot as plt
import os
import time
start_time = time.time()

# --- TOGGLES -------------------------------
justPrintFileNames = False
wFile = 4

def load_cdf(path):
    data_dict = stl.loadDictFromFile(path)
    data = deepcopy(data_dict['CuEDI_all_words'][0])
    minor = deepcopy(data_dict['minor_frame_idx'][0])
    major = deepcopy(data_dict['major_frame_idx'][0])
    epoch = deepcopy(data_dict['epoch'][0])
    return data, minor, major, epoch

def find_minor_frame_runs(minor):
    """
    Return (starts, values, lengths) for each contiguous run of a single
    Minor_frame_idx value. In this dataset every run is length 17.
    """
    change_idx = np.where(np.diff(minor) != 0)[0] + 1
    starts = np.concatenate(([0], change_idx))
    ends = np.concatenate((change_idx, [len(minor)]))
    values = minor[starts]
    lengths = ends - starts
    return starts, values, lengths

def get_even_minor_block_starts(minor):
    """
    Starting index of each 34-sample cycle, i.e. the start of every run
    where Minor_frame_idx is 0, 2, 4, 6, or 8 (the first half of a
    34-sample even/odd minor-frame pair).
    """
    starts, values, lengths = find_minor_frame_runs(minor)
    assert np.all(lengths == 17), "Expected every minor-frame run to be 17 samples"
    mask = np.isin(values, [0, 2, 4, 6, 8])
    return starts[mask]

def decode_word3_bitfields(raw_word3):
    """
    raw_word4: array of 16-bit raw values at word offset 3 (the "4th word").
    Bit layout (bit 15 = MSB):
      bit 14      -> HV/16
      bits 13:8   -> Step number (6 bits)
      bit 7       -> HV Enable
      bit 5       -> Test Pulse Enable
    """
    hv_16 = (raw_word3 >> 14) & 0b1
    step_number = (raw_word3 >> 8) & 0b111111
    hv_enable = (raw_word3 >> 7) & 0b1
    test_pulse_enable = (raw_word3 >> 5) & 0b1
    return hv_16, step_number, hv_enable, test_pulse_enable

def main(CDF_PATH):
    data, minor, major, epoch = load_cdf(CDF_PATH)

    starts = get_even_minor_block_starts(minor)  # one per 34-sample cycle

    # --- 1st word ---
    raw_word1 = data[starts + 0]
    Sync_Word = raw_word1

    # --- 2nd word ---
    raw_word2 = data[starts + 1]
    Status_word2 = raw_word2

    # --- 3rd word ---
    raw_word3 = data[starts + 2]
    Status_word3 = raw_word3
    hv_16, step_number, hv_enable, test_pulse = decode_word3_bitfields(raw_word3)

    # --- 4th word (offset 3): bitfields ---
    Status_word4 = data[starts + 3]

    # --- 5th word (offset 4): 12-bit field ---
    raw_word5 = data[starts + 4]
    ADC_stepper_vmon = raw_word5 & 0xFFF

    # --- 6th word ---
    raw_word6 = data[starts + 5]
    ADC_MCP_vmon = raw_word6 & 0xFFF

    # --- 7th word ---
    raw_word7 = data[starts + 6]
    ADC_MCP_Imon = raw_word7 & 0xFFF

    # --- 8th word ---
    raw_word8 = data[starts + 7]
    ADC_Stack_Vmon = raw_word8 & 0xFFF

    # --- 9th word ---
    raw_word9 = data[starts + 8]
    ADC_Stack_Imon = raw_word9 & 0xFFF

    # --- 10th word ---
    raw_word10 = data[starts + 9]
    ADC_3p3_Vmon = raw_word10 & 0xFFF

    # --- 11th word ---
    raw_word11 = data[starts + 10]
    ADC_5V_Vmon = raw_word11 & 0xFFF

    # --- 12th word ---
    raw_word12 = data[starts + 11]
    ADC_Temp_Vmon = raw_word12 & 0xFFF

    # --- words 13-33 (offsets 13-33): should always be zero ---
    counters = np.stack([data[starts + off] for off in range(12, 33)], axis=1).T
    # assert np.all(payload_tail == 0), "Unexpected nonzero value in words 13-33"

    # --- 34th word (offset 0): 625 kHz clock ---
    clock_word = data[starts+33]

    # --- TimeStamp ---
    cycle_dt = epoch[starts]

    data_dict = {
        "epoch": [cycle_dt,{'VAR_TYPE':'support_data'}],
        "counter22_625khz": [clock_word,{'DEPEND_0':'epoch','VAR_TYPE':'data'}],
        "hv_div16": [hv_16,{'DEPEND_0':'epoch','VAR_TYPE':'support_data'}],
        "step_number": [step_number,{'DEPEND_0':'epoch','VAR_TYPE':'support_data'}],
        "hv_enable": [hv_enable,{'DEPEND_0':'epoch','VAR_TYPE':'support_data'}],
        "test_pulse_enable": [test_pulse,{'DEPEND_0':'epoch','VAR_TYPE':'support_data'}],
        "Sync": [Sync_Word,{'DEPEND_0':'epoch','VAR_TYPE':'support_data'}],
        "Status_word2": [Status_word2, {'DEPEND_0': 'epoch', 'VAR_TYPE': 'support_data'}],
        "Status_word4": [Status_word4, {'DEPEND_0': 'epoch', 'VAR_TYPE': 'support_data'}],
        'ADC_stepper_vmon':[ADC_stepper_vmon,{'DEPEND_0': 'epoch', 'VAR_TYPE': 'data'}],
        'ADC_MCP_vmon': [ADC_MCP_vmon, {'DEPEND_0': 'epoch', 'VAR_TYPE': 'data'}],
        'ADC_MCP_Imon': [ADC_MCP_Imon, {'DEPEND_0': 'epoch', 'VAR_TYPE': 'support_data'}],
        'ADC_stack_vmon': [ADC_Stack_Vmon, {'DEPEND_0': 'epoch', 'VAR_TYPE': 'data'}],
        'ADC_stack_Imon': [ADC_Stack_Imon, {'DEPEND_0': 'epoch', 'VAR_TYPE': 'support_data'}],
        'ADC_3p3_vmon': [ADC_3p3_Vmon, {'DEPEND_0': 'epoch', 'VAR_TYPE': 'data'}],
        'ADC_5V_vmon': [ADC_5V_Vmon, {'DEPEND_0': 'epoch', 'VAR_TYPE': 'data'}],
        'ADC_temp_vmon':[ADC_Temp_Vmon,{'DEPEND_0': 'epoch', 'VAR_TYPE': 'data'}],
    }

    for i in range(21):
        data_dict[f'counter{i+1}'] = [counters[i],{'DEPEND_0': 'epoch', 'VAR_TYPE': 'data'}]

    return data_dict

if __name__ == "__main__":

    files = glob.glob(ProcessingClass.DIR + '/L0/CuEDI/' + '/*.cdf*')

    if justPrintFileNames:
        if len(files) == 0:
            raise Exception(f"There are no files in the directory ({ProcessingClass.DIR})")
        else:
            for idx, thing in enumerate(files):
                print(f'[{idx}] {os.path.basename(thing)}')
    else:
        stl.prgMsg(f'Extracting L0 CuEDI data')
        data_dict_output = main(files[wFile])
        outputFilePath = f'{ProcessingClass.DIR}/L1/CuEDI/{os.path.basename(files[wFile]).replace("l0","l1")}'
        stl.outputDataDict(outputPath=outputFilePath,
                           data_dict=data_dict_output)
        stl.Done(start_time)