import numpy as np
class ProcessingClass:

    # --- Pathing ---------------------------------------------------------------
    DIR = 'C:/Users/cfelt/OneDrive - University of Iowa/rockets/OCHRE/data/INT/'
    SOURCE = 'simulator/'
    # SOURCE = 'payload/'

    # --- Instrument Words ---
    instr_dict = {
        'CuEDI': {'rows': None, 'cols': [10, 11, 21, 22, 36, 37, 52, 53, 54, 70, 71, 81, 82, 96, 97, 112, 113]},
        'LP':{'rows':None,'cols':[6,7,19,20,34,35,50,51,66,67,79,80,94,95,110,111]},
        'SCM':{'rows':None,'cols':np.array([1,2,3,
                                            16,17,18,
                                            31,32,33,
                                            46,47,48,
                                            61,62,63,
                                            76,77,78,
                                            91,92,93,
                                            106,107,108])},
    }