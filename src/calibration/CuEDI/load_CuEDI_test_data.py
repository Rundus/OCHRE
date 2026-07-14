import h5py
import numpy as np
import spaceToolsLib as stl

path_to_file = '/home/connor/PycharmProjects/OCHRE/src/calibration/CuEDI/'
file_name = 'UIOWA_OCHRE_CuEDI_testing_07122026_v0.h5'
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

    stl.outputDataDict(data_dict=data_dict_output,
                       outputPath=path_to_file+file_name.replace('.h5','.cdf'))