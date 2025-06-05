import numpy as np

def calc_LFlow_from_residence_time(columnHeight, residenceTime):
    try:
        chargeFlow = float(columnHeight)/(float(residenceTime)/60)
        return chargeFlow
    except:
        return 0
    

def calc_LFlow(columnHeight, columnDiameter, contactTime):
    try:
        CSA = (float(columnDiameter)**2*np.pi)/4
        CV =  (float(columnHeight)*CSA)/1000
        volumeOfBuffer = float(CV)*2
        VFlow = (volumeOfBuffer/float(contactTime))*60
        LFlow = (VFlow/CSA)*1000

        return{
            "columnVolume": CV,
            "linearFlow": LFlow
        }
    except:
        return{
                "columnVolume": '',
                "linearFlow": ''
            }