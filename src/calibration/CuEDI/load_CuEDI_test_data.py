import h5py
import numpy as np
import spaceToolsLib as stl

path_to_file = '/home/connor/Data/ROCKETS/OCHRE/calibration/CuEDI/'
# file_name = 'UIOWA_OCHRE_CuEDI_testing_07122026_v0.h5'
file_name = 'UIOWA_OCHRE_CuEDI_testing_07222026_v0.h5'
# Open the file in read mode

data_dict_output = {}
with h5py.File(path_to_file + file_name, 'r') as f:
    # List all top-level groups/datasets
    print("Keys:", list(f.keys()))

    dataKeys = f.keys()
    for key in dataKeys:
        data_dict_output={**data_dict_output,
                          **{key:[np.array(f[key][:][0]),{}]}
                          }

    # [1] Add VAR_TYPE: 'support_data' to every variable's metadata
    for key in data_dict_output:
        data_dict_output[key][1]['VAR_TYPE'] = 'support_data'

    # [2] and [3] For variables ending in '_Data', override VAR_TYPE and add DEPEND_0
    for key in data_dict_output:
        if key.endswith('_Data'):
            data_dict_output[key][1]['VAR_TYPE'] = 'data'
            data_dict_output[key][1]['UNITS'] = 'ADC Value'
            data_dict_output[key][1]['LABLAXIS'] = key.replace('eepaa_','').replace('_Data','')
            corresponding_time_key = key.replace('_Data', '_Time_100nS')
            data_dict_output[key][1]['DEPEND_0'] = corresponding_time_key
        elif key.endswith('_Time_100nS'):
            data_dict_output[key][0] = (data_dict_output[key][0]- 1.75940E14)/(1E7)

    stl.outputDataDict(data_dict=data_dict_output,
                       outputPath=path_to_file+file_name.replace('.h5','.cdf'))