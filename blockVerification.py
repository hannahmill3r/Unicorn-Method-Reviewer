from proAMainLoop import calc_LFlow
from extractText import closest_match_unit_op

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
        pfcQD = ' '
        for key in pfcData.keys():
            if block['settings']['inlet_setting'] == pfcData[key]['inlet']:
                if pfcData[key]['qd'].strip() != '' and pfcData[key]['direction'].strip() != '' and pfcData[key]['flow_rate'] != '':
                    pfcQD = pfcData[key]['qd']
                pass    
            #methodQD = pfcData[block['settings']['inlet_setting']]['qd']


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
        if pfcQD != block["settings"]['inlet_QD_setting'] and pfcQD.strip()!='': 
            incorrectFieldText.append(f"Expected {pfcQD}")
            incorrectField = True
        #other settings check

        if incorrectField:
            highlights.append({
                "blockData": block, 
                "annotationText": incorrectFieldText
            })

    for key in pfcData.keys():
        if purge_blocks[-1]['settings']['inlet_setting'] == pfcData[key]['inlet']:
            if pfcData[key]['qd'].strip() != '' and pfcData[key]['direction'].strip() != '' and pfcData[key]['flow_rate'] != '':
                pfcQD = pfcData[key]['qd']



    
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
    if  pfcQD != purge_blocks[-1]["settings"]['inlet_QD_setting']:
        incorrectFieldText.append(f"Expected {pfcQD}")
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
        methodQD = pfcData['Equilibration']['qd']


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

    equilLFlow = calc_LFlow(float(columnParam["columnHeight"]), float(columnParam["columnDiameter"]), float(columnParam["contactTime"]))["linearFlow"]
    for block in indiv_blocks:
        incorrectFieldText = []
        incorrectField = False
        direct = pfcQD = residenceTime = flowRate= ''
        closestMatch, ratio = closest_match_unit_op(block['blockName'], pfcData.keys())


        for key in pfcData.keys():

            if 'rinse' in block['blockName'].lower() and pfcData.get(key).get('inlet') == block['settings']['inlet_setting']:
                pfcQD = pfcData[key]['qd']
                direct = pfcData[key]['direction']
                flowRate = pfcData[key]['flow_rate']
                residenceTime = pfcData[key]['residence time']

            elif key == closestMatch and "rinse" not in block['blockName'].lower():
                pfcQD = pfcData[key]['qd']
                direct = pfcData[key]['direction']
                flowRate = pfcData[key]['flow_rate']
                residenceTime = pfcData[key]['residence time']


        if "flush" in block['blockName'].lower():
            if "Bypass" not in block["settings"]['column_setting']:
                incorrectFieldText.append(f"Expected Bypass")
                incorrectField = True
            if block["settings"]['manflow'] != ' ' and block["settings"]['manflow'] != 60.0:
                incorrectFieldText.append("Expected 60% manflow")
                incorrectField = True

        elif direct.strip() != '':
            if direct.lower() not in block["settings"]['column_setting'].lower():
                incorrectFieldText.append(f"Expected {direct}")
                incorrectField = True
        if "Inline" not in block["settings"]['filter_setting']:
            incorrectFieldText.append("Expected Inline filter")
            incorrectField = True
        if "Inline" not in block["settings"]['bubbletrap_setting']:
            incorrectFieldText.append("Expected bubbletrap bypass")
            incorrectField = True

        #all outlets go to wast EXCEPT for elution
        if "Waste" not in block["settings"]['outlet_setting'] and "watch_uv" not in block['blockName'].lower():
            incorrectFieldText.append("Expected waste outlet")
            incorrectField = True
        elif "MS_Outlet" not in block["settings"]['outlet_setting'] and "watch_uv" in block['blockName'].lower():
            incorrectFieldText.append("Elution should go to MS outlet")
            incorrectField = True

        if "," in block['settings']['flow_setting']:
            listOfFlows = block['settings']['flow_setting'].strip().split(",")

            for i in range(len(listOfFlows)):
                flow = float(listOfFlows[i])
                tag = block['settings']['flow_tags'][i]

                if ("sani" in tag.lower() or "first_cv_equil" in tag.lower()):
                    if flow != round(equilLFlow) and flow != round(equilLFlow, 1) and flow != round(equilLFlow, 2):
                        incorrectFieldText.append(f"Expected {round(equilLFlow, 2)} for pre sani flow rate")
                        incorrectField = True
                elif flowRate.strip()!='':
                    if ("wash" in block["blockName"].lower() and "1" in block["blockName"].lower()) or "charge" in block["blockName"].lower():
                        resTimeLFlow = calc_LFlow_from_residence_time(float(columnParam["columnHeight"]), float(residenceTime))
                        if flow != round(resTimeLFlow) and flow != round(resTimeLFlow, 1) and flow != round(resTimeLFlow, 2):
                            incorrectFieldText.append(f"Expected {round(resTimeLFlow, 2)} for flow rate")
                            incorrectField = True
                    elif round(flow) != round(float(flowRate)):
                        incorrectFieldText.append("Unexpected Flow Value")
                        incorrectField = True
                #TODO: ELSE wash 1 or charge has a seperate flow rate

        elif ("sani" in block['settings']['flow_tags'][0].lower() or "first_cv_equil" in block['settings']['flow_tags'][0].lower()):
            if round(equilLFlow) != float(block['settings']['flow_setting']) and round(equilLFlow, 1) != float(block['settings']['flow_setting']) and round(equilLFlow, 2) != float(block['settings']['flow_setting']):
                incorrectFieldText.append(f"Expected {round(equilLFlow, 2)} flow")
                incorrectField = True
        elif flowRate.strip()!='':
            if ("wash" in block["blockName"].lower() and "1" in block["blockName"].lower()) or "charge" in block["blockName"].lower():
                    flow = float(block['settings']['flow_setting'])
                    resTimeLFlow = calc_LFlow_from_residence_time(float(columnParam["columnHeight"]), float(residenceTime))

                    if flow != round(resTimeLFlow) and flow != round(resTimeLFlow, 1) and flow != round(resTimeLFlow, 2):
                        incorrectFieldText.append(f"Expected {round(resTimeLFlow, 2)} for flow rate")
                        incorrectField = True
            elif float(block['settings']['flow_setting']) != float(flowRate):
                incorrectFieldText.append(f"Expected {(pfcData[block['settings']['inlet_setting']]['flow_rate'])} flow")
                incorrectField = True

        if "flush" in block["blockName"].lower():
            match, ratio = closest_match_unit_op(block['settings']['setmark_setting'], [block["blockName"]])

            if ratio < .20:
                incorrectFieldText.append("Please double check setmark naming, similarity score was low")
                incorrectField = True

        elif block['settings']['setmark_setting'] not in block["blockName"]:
            incorrectFieldText.append("Incorrect setmark naming")
            incorrectField = True

        if ((block['settings']['snapshot_setting'] != block['settings']['setmark_setting'] + " End") and (block['settings']['snapshot_setting'] != block['settings']['setmark_setting'] + "_End")) and block['settings']['snapshot_setting'] != " ":
            incorrectFieldText.append("Incorrect snapshot naming")
            incorrectField = True
        #pump A
        if "flush" not in block['blockName'].lower():
            if "rinse" in block['blockName'].lower() or "wash_1" in block['blockName'].lower() or "wash_3" in block['blockName'].lower() or "equil" in block['blockName'].lower() or "elution" in block['blockName'].lower() or "charge" in block['blockName'].lower():
                if ("pa" not in block['settings']['reset_setting'].lower()):
                    incorrectFieldText.append("Totalizer should be reset through pump A")
                    incorrectField = True
            #pump B
            else:
                if ("pb" not in block['settings']['reset_setting'].lower()):
                    incorrectFieldText.append("Totalizer should be reset through pump B")
                    incorrectField = True
            
        #TODO: check inlets?

        if incorrectField:
            highlights.append({
                "blockData": block, 
                "annotationText": incorrectFieldText
            })

    return highlights

def check_watch_settings(block):

    highlights = []
    incorrectField = False

    incorrectFieldText = []
    incorrectField = False

    #all outlets go to wast EXCEPT for elution
    if  "MS_Outlet" not in block["settings"]['outlet_setting']:
        incorrectFieldText.append("Elution should go to MS outlet")
        incorrectField = True

    if block['settings']['backside_setting'] >= block['settings']['peak_protect_setting']:
        incorrectFieldText.append("Peak protection should be greater than backside cut.")
        incorrectField = True

    if incorrectField:
        highlights.append({
            "blockData": block, 
            "annotationText": incorrectFieldText
        })

    return highlights


#TODO: add scouting run checks


def calc_LFlow_from_residence_time(columnHeight, residenceTime):
    try:
        chargeFlow = float(columnHeight)/(float(residenceTime)/60)
        return chargeFlow
    except:
        return 0
