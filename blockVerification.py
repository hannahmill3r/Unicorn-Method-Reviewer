from proAMainLoop import calc_LFlow
def check_column_params(methodsColumnParams, pfcColumnParams):
    highlights = []
    incorrectField = False

    methodH = methodsColumnParams["columnData"][ "columnHeight"]
    methodD = methodsColumnParams["columnData"][ "columnDiameter"]
    methodCV = methodsColumnParams["columnData"][ "columnVolume"]

    pfcH = pfcColumnParams['columnHeight']
    pfcD = pfcColumnParams["columnDiameter"]
    pfcContactTime = pfcColumnParams["contactTime"]
    pfcClac = calc_LFlow(float(pfcH), float(pfcD), float(pfcContactTime))

    pfcCV = pfcClac["columnVolume"]
    

    incorrectFieldText = []
    incorrectField = False

    if methodH !=pfcH:
        incorrectFieldText.append(f"Incorrect column height, expected {pfcH}")
        incorrectField = True
    if methodD !=pfcD:
        incorrectFieldText.append(f"Incorrect column diameter, expected {pfcD}")
        incorrectField = True
    if methodCV != (f'{pfcCV:.3f}') and methodCV != (f'{pfcCV:.2f}'):
        if methodD !=pfcD:
            incorrectFieldText.append(f"Incorrect column volume, expected {pfcCV:.3f}. Likely due to incorrect column diameter")
        if methodH !=pfcH:
            incorrectFieldText.append(f"Incorrect column volume, expected {pfcCV:.3f}. Likely due to incorrect column height")
        else:
            incorrectFieldText.append(f"Incorrect column volume, expected {pfcCV:.3f}")
        incorrectField = True
    

    if incorrectField:
        highlights.append({
            "blockData": methodsColumnParams, 
            "annotationText": incorrectFieldText
        })

    return highlights


def check_purge_block_settings(purge_blocks, pfcData):
    highlights = []
    incorrectField = False
    firstBlock = True

    for block in purge_blocks[:-1]:

        incorrectFieldText = []
        incorrectField = False
        methodQD = pfcData[block['settings']['inlet_setting']]['qd']


        if firstBlock == True:
            firstBlock = False
            if "downflow" not in block["settings"]['column_setting'].lower() and "upflow" not in block["settings"]['column_setting'].lower():
                incorrectFieldText.append("Expected column bypass")
                incorrectField = True
        else:
            if "Bypass" not in block["settings"]['column_setting']:
                incorrectFieldText.append("Expected column bypass")
                incorrectField = True

        if block['settings']['manflow']!= 60.0:
            incorrectFieldText.append("Expected 60% ManFlow")
            incorrectField = True
        if "Bypass" not in block["settings"]['bubbletrap_setting']:
            incorrectFieldText.append("Expected bubbletrap bypass")
            incorrectField = True
        if "Waste" not in block["settings"]['outlet_setting']:
            incorrectFieldText.append("All purges should go to waste")
            incorrectField = True
        if methodQD != block["settings"]['inlet_QD_setting']:
            
            incorrectFieldText.append(f"Expected {methodQD}")
            incorrectField = True
        #other settings check

        if incorrectField:
            highlights.append({
                "blockData": block, 
                "annotationText": incorrectFieldText
            })

    methodQD = pfcData[purge_blocks[-1]['settings']['inlet_setting']]['qd']


    
    if purge_blocks[-1]['settings']['manflow']!= 60.0:
        incorrectFieldText.append("Expected 60% ManFlow")
        incorrectField = True
    if "Bypass" not in purge_blocks[-1]["settings"]['column_setting']:
        incorrectFieldText.append("Expected column bypass")
        incorrectField = True
    if "Inline" not in purge_blocks[-1]["settings"]['bubbletrap_setting']:
        incorrectFieldText.append("Expected bubbletrap bypass")
        incorrectField = True
    if 20.0 != purge_blocks[-1]["settings"]['end_block_setting']:
        incorrectFieldText.append("Expected 20.0 volume purge")
        incorrectField = True
    if  methodQD != purge_blocks[-1]["settings"]['inlet_QD_setting']:
        incorrectFieldText.append(f"Expected {methodQD}")
        incorrectField = True


    if incorrectField:
        highlights.append({
            "blockData": purge_blocks[-1], 
            "annotationText": incorrectFieldText
        })

    return highlights



def check_MS_blocks_settings_pdf(MS_blocks, pfcData, numberofMS):
    highlights = []
    incorrectField = False
    firstBlock = True

    for block in MS_blocks:

        incorrectFieldText = []
        incorrectField = False
        methodQD = pfcData[block['settings']['inlet_setting']]['qd']



        if "Bypass" not in block["settings"]['column_setting']:
            incorrectFieldText.append("Expected column bypass")
            incorrectField = True
        if "Inline" not in block["settings"]['filter_setting']:
            incorrectFieldText.append("Expected Inline filter")
            incorrectField = True
        if int(block["settings"]['fraction_setting'])*5 != block["settings"]['end_block_setting']:
            incorrectFieldText.append("Expected final volume to be 5 x (# of mainstreams)")
            incorrectField = True
        if int(block["settings"]['fraction_setting']) != int(numberofMS):
            incorrectFieldText.append(f"Expected number of mainstreams to be: {numberofMS}")
            incorrectField = True
        if block['settings']['manflow']!= 60.0:
            incorrectFieldText.append("Expected 60% ManFlow")
            incorrectField = True
        if "Inline" not in block["settings"]['bubbletrap_setting']:
            incorrectFieldText.append("Expected bubbletrap bypass")
            incorrectField = True
        if methodQD != block["settings"]['inlet_QD_setting']:
            
            incorrectFieldText.append(f"Expected {methodQD}")
            incorrectField = True
        #other settings check

        if incorrectField:
            highlights.append({
                "blockData": block, 
                "annotationText": incorrectFieldText
            })

    return highlights

def check_indiv_blocks_settings_pdf(indiv_blocks, pfcData, columnParam):
    highlights = []
    incorrectField = False

    LFlow = calc_LFlow(float(columnParam["columnHeight"]), float(columnParam["columnDiameter"]), float(columnParam["contactTime"]))["linearFlow"]

    for block in indiv_blocks:
        incorrectFieldText = []
        incorrectField = False

        direct = pfcData[block['settings']['inlet_setting']]['direction']

        if direct.lower() not in block["settings"]['column_setting'].lower():
            incorrectFieldText.append(f"Expected {direct}")
            incorrectField = True
        if "Inline" not in block["settings"]['filter_setting']:
            incorrectFieldText.append("Expected Inline filter")
            incorrectField = True
        if "Inline" not in block["settings"]['bubbletrap_setting']:
            incorrectFieldText.append("Expected bubbletrap bypass")
            incorrectField = True
        if "Waste" not in block["settings"]['outlet_setting']:
            incorrectFieldText.append("Expected waste outlet")
            incorrectField = True
        if round(LFlow) != float(block['settings']['flow_setting']) and round(LFlow, 1) != float(block['settings']['flow_setting']) and round(LFlow, 2) != float(block['settings']['flow_setting']):
            incorrectFieldText.append(f"Expected {round(LFlow, 2)} flow")
            incorrectField = True
        if block['settings']['setmark_setting'] not in block["blockName"]:
            incorrectFieldText.append("Incorrect setmark naming")
            incorrectField = True
        if block['settings']['snapshot_setting'] != block['settings']['setmark_setting'] + " End":
            incorrectFieldText.append("Incorrect snapshot naming")
            incorrectField = True

        #TODO: add totalizer reset and insure correct pump is used

        if incorrectField:
            highlights.append({
                "blockData": block, 
                "annotationText": incorrectFieldText
            })

    return highlights

#TODO: add elution checks

#TODO: add scouting run checks