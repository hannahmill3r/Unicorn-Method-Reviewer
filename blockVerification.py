from extractText import closest_match_unit_op
import re
import math
from flowCalculations import calc_LFlow, calc_LFlow_from_residence_time



def check_column_params(methodsColumnParams, pfcColumnParams):
    highlights = []

    methodH = methodsColumnParams["columnData"][ "columnHeight"]
    methodD = methodsColumnParams["columnData"][ "columnDiameter"]
    methodCV = methodsColumnParams["columnData"][ "columnVolume"]

    pfcH = pfcColumnParams['columnHeight']
    pfcD = pfcColumnParams["columnDiameter"]
    pfcContactTime = pfcColumnParams["contactTime"]
    pfcClac = calc_LFlow(float(pfcH), float(pfcD), float(pfcContactTime))

    pfcCV = pfcClac["columnVolume"]
    

    incorrectFieldText = []

    if methodH !=pfcH:
        incorrectFieldText.append(f"Incorrect column height, expected {pfcH}")
          
    if methodD !=pfcD:
        incorrectFieldText.append(f"Incorrect column diameter, expected {pfcD}")
          
    if methodCV != (f'{pfcCV:.3f}') and methodCV != (f'{pfcCV:.2f}'):
        if methodD !=pfcD:
            incorrectFieldText.append(f"Incorrect column volume, expected {pfcCV:.3f}. Likely due to incorrect column diameter")
        if methodH !=pfcH:
            incorrectFieldText.append(f"Incorrect column volume, expected {pfcCV:.3f}. Likely due to incorrect column height")
        else:
            incorrectFieldText.append(f"Incorrect column volume, expected {pfcCV:.3f}")
          

    if incorrectFieldText:
        highlights.append({
            "blockData": methodsColumnParams, 
            "annotationText": incorrectFieldText
        })

    return highlights


def check_purge_block_settings(purge_blocks, pfcData):
    """
    Check purge method block data against the user entered pfc data 
    
    Args:
        purge_blocks (dict): Contains all relevant data to the code block, such as name, manflow, linear flow rate, etc.
        pfcData (dict): Contains all pfc input data from the user for all inlets, (equil, charge, post sani, etc.)
        
    Returns:
        highlights (dict): list of highlight block dictionary and the error messages associated with the block
    """
        
    highlights = []
    firstBlock = True

    #analyse pump a and b seperately, time based blocks dont have anything we validate so remove them from other purge blocks as well
    for block in purge_blocks[::-1]:
        if 'purge_a_pump' in block['blockName'].lower():
            purge_blocks.remove(block)

            if block['settings']['manflow']!= 60.0:
                incorrectFieldText.append("Expected 60% ManFlow")
                  
            if"Inline" not in block["settings"]['bubbletrap_setting']:
                incorrectFieldText.append("Expected bubbletrap bypass")
                  
            if "Waste" not in block["settings"]['outlet_setting']:
                incorrectFieldText.append("All purges should go to waste")
                  
            if "Inlet 1" != block["settings"]['inlet_setting']: 
                incorrectFieldText.append(f"Expected Inlet 1")
                  
            if "Bypass" not in block["settings"]['column_setting']:
                incorrectFieldText.append("Expected column bypass")
                  
            if block['settings']['filter_setting']!= "Inline":
                incorrectFieldText.append("Expected inline filter")
                  
            if "time" not in block['settings']['base_setting'].lower():
                incorrectFieldText.append("Expected Pump A purge to be in time")
                  

        elif 'purge_b_pump' in block['blockName'].lower():
            purge_blocks.remove(block)
            
            if block['settings']['manflow']!= 60.0:
                incorrectFieldText.append("Expected 60% ManFlow")
                  
            if"Bypass" not in block["settings"]['bubbletrap_setting']:
                incorrectFieldText.append("Expected bubbletrap bypass")
                  
            if "Waste" not in block["settings"]['outlet_setting']:
                incorrectFieldText.append("All purges should go to waste")
                  
            if "Inlet 7" != block["settings"]['inlet_setting']: 
                incorrectFieldText.append(f"Expected Inlet 7")
                  
            if "Bypass" not in block["settings"]['column_setting']:
                incorrectFieldText.append("Expected column bypass")
                  
            if block['settings']['filter_setting']!= "Bypass":
                incorrectFieldText.append("Expected bypass filter")
                  
            if "time" not in block['settings']['base_setting'].lower():
                incorrectFieldText.append("Expected Pump B purge to be in time")
                  
        elif re.search('time', block['settings']['base_setting'].lower()):
            purge_blocks.remove(block)


            
    #All blocks except for the final blocks are processed similarly, final block is seperate
    for blockCounter, block in enumerate(purge_blocks):

        incorrectFieldText = []

        #grab the QD for the current inlet from the pfc data dict
        pfcQD = ' '
        for key in pfcData.keys():
            if block['settings']['inlet_setting'] == pfcData[key]['inlet']:
                if pfcData[key]['qd'].strip() != '' and pfcData[key]['direction'].strip() != '' and pfcData[key]['flow_rate'] != '':
                    pfcQD = pfcData[key]['qd']
                pass    

        #first block column settings should be upflow and downflow, all other blocks should be bypass
        if firstBlock == True:
            firstBlock = False
            if "downflow" not in block["settings"]['column_setting'].lower() and "upflow" not in block["settings"]['column_setting'].lower():
                incorrectFieldText.append("Expected column bypass")

        else:
            if "Bypass" not in block["settings"]['column_setting']:
                incorrectFieldText.append("Expected column bypass")

        #Check all other settings, all inlets should be set to bypass and waste. Manflow and QD setting should match pfc provided information
        #TODO: the manflow is hard coded and needs to be extracted based on the sharepoint file linked

        if blockCounter!= len(purge_blocks)-1:
            if "Bypass" not in block["settings"]['bubbletrap_setting']:
                incorrectFieldText.append("Expected bubbletrap bypass")
                
            if "Waste" not in block["settings"]['outlet_setting']:
                incorrectFieldText.append("All purges should go to waste")
                  

        else:
            if "Inline" not in block["settings"]['bubbletrap_setting']:
                incorrectFieldText.append("Expected bubbletrap bypass")
                  
            if float(20.0) != float(block["settings"]['end_block_setting']):
                incorrectFieldText.append("Expected 20.0 volume purge")
                  
            if "Bypass" not in block["settings"]['column_setting']:
                incorrectFieldText.append("Expected column bypass")
                  

        if  pfcQD != block["settings"]['inlet_QD_setting']:
            incorrectFieldText.append(f"Expected {pfcQD}")
              
        if block['settings']['manflow']!= 60.0:
            incorrectFieldText.append("Expected 60% ManFlow")
              
        if incorrectFieldText:
            highlights.append({
                "blockData": block, 
                "annotationText": incorrectFieldText
            })

    return highlights



def check_MS_blocks_settings_pdf(MS_blocks, pfcData, numberofMS):
    highlights = []

    for block in MS_blocks:

        incorrectFieldText = []
        methodQD = pfcData['Equilibration']['qd']

        if "Bypass" not in block["settings"]['column_setting']:
            incorrectFieldText.append("Expected column bypass")
            
        if "Inline" not in block["settings"]['filter_setting']:
            incorrectFieldText.append("Expected Inline filter")
            
        if float(block["settings"]['fraction_setting'])*5 != float(block["settings"]['end_block_setting']):
            incorrectFieldText.append("Expected final volume to be 5 x (# of mainstreams), got, "+ block["settings"]['end_block_setting'])
            
        if int(block["settings"]['fraction_setting']) != int(numberofMS):
            incorrectFieldText.append(f"Expected number of mainstreams to be: {numberofMS}")
            
        if block['settings']['manflow']!= 60.0:
            incorrectFieldText.append("Expected 60% ManFlow")
            
        if "Inline" not in block["settings"]['bubbletrap_setting']:
            incorrectFieldText.append("Expected bubbletrap bypass")

        if methodQD != block["settings"]['inlet_QD_setting']: 
            incorrectFieldText.append(f"Expected {methodQD}")
             
        if incorrectFieldText !=[]:
            highlights.append({
                "blockData": block, 
                "annotationText": incorrectFieldText
            })
    print("MS", highlights)
    return highlights

def check_indiv_blocks_settings_pdf(indiv_blocks, pfcData, columnParam):
    highlights = []

    equilLFlow = calc_LFlow(float(columnParam["columnHeight"]), float(columnParam["columnDiameter"]), float(columnParam["contactTime"]))["linearFlow"]
    for index, block in enumerate(indiv_blocks):
        incorrectFieldText = []
        direct = pfcQD = residenceTime = flowRate= ''
        closestTitleMatch, ratio = closest_match_unit_op(block['blockName'], pfcData.keys())
        closesTagMatch, ratioTag = closest_match_unit_op(block['settings']['flow_tags'][-1].split('_Flowrate')[0], pfcData.keys())


        if (closesTagMatch!=closestTitleMatch):
            if "rinse" in block['blockName'].lower():
                closestTitleMatch, ratnew = closest_match_unit_op(block['settings']['flow_tags'][-1].split('_Flowrate')[0]+" Rinse", pfcData.keys())

        for key in pfcData.keys():
            if key == closestTitleMatch :
                pfcQD = pfcData[key]['qd']
                direct = pfcData[key]['direction']
                flowRate = pfcData[key]['flow_rate']
                residenceTime = pfcData[key]['residence time']
                CV = pfcData[key]['CV']

        
        #TODO: are there common enough checks like this that we can add a helper function that will check bubbletrap, filter and manflow automatically?     
        if "Inline" not in block["settings"]['filter_setting']:
            incorrectFieldText.append("Expected Inline filter")
              
        if "Inline" not in block["settings"]['bubbletrap_setting']:
            incorrectFieldText.append("Expected bubbletrap bypass")
              

        #all outlets go to wast EXCEPT for elution
        if "Waste" not in block["settings"]['outlet_setting'] and "watch_uv" not in block['blockName'].lower():
            incorrectFieldText.append("Expected waste outlet")

        #TODO: check that this can be removed     
        #elif "MS_Outlet" not in block["settings"]['outlet_setting'] and "watch_uv" in block['blockName'].lower():
            #incorrectFieldText.append("Elution should go to MS outlet")
              
        #TODO: this is definetly redundant, have ai clean
        if "," in block['settings']['flow_setting']:
            listOfFlows = block['settings']['flow_setting'].strip().split(",")

            for i in range(len(listOfFlows)):
                flow = float(listOfFlows[i])
                tag = block['settings']['flow_tags'][i]

                if ("sani" in tag.lower() or "first_cv_equil" in tag.lower()):
                    if flow != round(equilLFlow) and flow != round(equilLFlow, 1) and flow != round(equilLFlow, 2):
                        incorrectFieldText.append(f"Expected {round(equilLFlow, 2)} for pre sani flow rate")
                          
                elif flowRate.strip()!='':
                    if ("wash" in block["blockName"].lower() and "1" in block["blockName"].lower()) or "charge" in block["blockName"].lower():
                        resTimeLFlow = calc_LFlow_from_residence_time(float(columnParam["columnHeight"]), float(residenceTime))
                        if flow != round(resTimeLFlow) and flow != round(resTimeLFlow, 1) and flow != round(resTimeLFlow, 2):
                            incorrectFieldText.append(f"Expected {round(resTimeLFlow, 2)} for flow rate")
                              
                    elif round(flow) != round(float(flowRate)):
                        incorrectFieldText.append("Unexpected Flow Value")
                          

        elif ("sani" in block['settings']['flow_tags'][0].lower() or "first_cv_equil" in block['settings']['flow_tags'][0].lower()):
            if round(equilLFlow) != float(block['settings']['flow_setting']) and round(equilLFlow, 1) != float(block['settings']['flow_setting']) and round(equilLFlow, 2) != float(block['settings']['flow_setting']):
                incorrectFieldText.append(f"Expected {round(equilLFlow, 2)} flow")
                  
        elif flowRate.strip()!='':
            if ("wash" in block["blockName"].lower() and "1" in block["blockName"].lower()) or "charge" in block["blockName"].lower():
                    flow = float(block['settings']['flow_setting'])
                    resTimeLFlow = calc_LFlow_from_residence_time(float(columnParam["columnHeight"]), float(residenceTime))

                    if flow != round(resTimeLFlow) and flow != round(resTimeLFlow, 1) and flow != round(resTimeLFlow, 2):
                        incorrectFieldText.append(f"Expected {round(resTimeLFlow, 2)} for flow rate")
                          
            elif float(block['settings']['flow_setting']) != float(flowRate):
                incorrectFieldText.append(f"Expected {(pfcData[block['settings']['inlet_setting']]['flow_rate'])} flow")
                  

        if "flush" in block["blockName"].lower():
            match, ratio = closest_match_unit_op(block['settings']['setmark_setting'], [block["blockName"]])
            if ratio < .20:
                incorrectFieldText.append("Please double check setmark naming, similarity score was low")
            if "Bypass" not in block["settings"]['column_setting']:
                incorrectFieldText.append(f"Expected Bypass")
            if block["settings"]['manflow'] != ' ' and block["settings"]['manflow'] != 60.0:
                incorrectFieldText.append("Expected 60% manflow")
        
        #Flushes do not have a totalizer reset
        else:
            #Check buffers that should be reset through wash pump A
            if "rinse" in block['blockName'].lower() or "wash_1" in block['blockName'].lower() or "wash_3" in block['blockName'].lower() or "equil" in block['blockName'].lower() or "elution" in block['blockName'].lower() or "charge" in block['blockName'].lower():
                if ("pa" not in block['settings']['reset_setting'].lower()):

                    #Blocks will sometime's share previous buffer settings if they have the same QD
                    if (indiv_blocks[index-1]['settings']['inlet_QD_setting'] != block['settings']['inlet_QD_setting']) and 'pa' not in indiv_blocks[index-1]['settings']['reset_setting'].lower():
                        incorrectFieldText.append("Totalizer should be reset through pump A")
                          

            #Check buffers that should be reset through wash pump B
            else:
                if ("pb" not in block['settings']['reset_setting'].lower()):
                    #Blocks will sometime's share previous buffer settings if they have the same QD
                    if (indiv_blocks[index-1]['settings']['inlet_QD_setting'] != block['settings']['inlet_QD_setting']) and 'pb' not in indiv_blocks[index-1]['settings']['reset_setting'].lower():
                        incorrectFieldText.append("Totalizer should be reset through pump B")
                  
            if block['settings']['setmark_setting'] not in block["blockName"]:
                incorrectFieldText.append("Incorrect setmark naming")
            if direct.strip() != '' and direct.lower() not in block["settings"]['column_setting'].lower():
                incorrectFieldText.append(f"Expected {direct}")
        
        if ((block['settings']['snapshot_setting'] != block['settings']['setmark_setting'] + " End") and (block['settings']['snapshot_setting'] != block['settings']['setmark_setting'] + "_End")) and block['settings']['snapshot_setting'] != " ":
            incorrectFieldText.append("Incorrect snapshot naming")      

        #check the end block breakpoint column volumes
        try:
            if float(block['settings']['end_block_setting'])!= float(CV) and 'flush' not in block['blockName'].lower():
                incorrectFieldText.append(f"Expected {CV} breakpoint volume")
                  
            if 'flush' in block['blockName'].lower() and float(block['settings']['end_block_setting'])!= float(20.0):
                block['settings']['end_block_setting']
                incorrectFieldText.append(f"Expected flush to have 20.0 breakpoint volume")
                  
        except:
            incorrectFieldText.append(f"I was unable to process the formatting for the breakpoint volume, please double check it")
              
        #check the snapshot breakpoint column volumes
        try:
            if 'flush' not in block['blockName'].lower():
                if float(block['settings']['snapshot_breakpoint_setting'])!= float(CV):
                    incorrectFieldText.append(f"Expected {CV} breakpoint volume for snapshot")
                      
        except:
            incorrectFieldText.append(f"I was unable to process the formatting for the snapshot breakpoint volume, please double check it")
              
        #TODO: check inlets?

        if incorrectFieldText:
            highlights.append({
                "blockData": block, 
                "annotationText": incorrectFieldText
            })

    return highlights

def check_watch_settings(block):

    highlights = []
    incorrectFieldText = []

    #all outlets go to waste EXCEPT for elution
    if  "MS_Outlet" not in block["settings"]['outlet_setting']:
        incorrectFieldText.append("Elution should go to MS outlet")
          

    if block['settings']['backside_setting'] >= block['settings']['peak_protect_setting']:
        incorrectFieldText.append("Peak protection should be greater than backside cut.")
          

    if incorrectFieldText:
        highlights.append({
            "blockData": block, 
            "annotationText": incorrectFieldText
        })

    return highlights

def check_end_of_run_pdf(finalBlock):
    highlights = []
    incorrectFieldText = []
    print(finalBlock)
    
    if "time" not in finalBlock["settings"]["base_setting"].lower():
        incorrectFieldText.append("Expected base to be in time")
          
    if 'end_of_run_delay' not in finalBlock["blockName"].lower():
        incorrectFieldText.append("Final Block should be the end of run delay")
          
    if float(0) == float(finalBlock["settings"]["end_block_setting"]):
        incorrectFieldText.append("End of run delay requires a non zero amount of time for data transfer to server")
          
    if incorrectFieldText:
        highlights.append({
            "blockData": finalBlock, 
            "annotationText": incorrectFieldText
        })
    return highlights
        
def check_scouting(scoutingData, pfcData, uvPreset, numOfCycles, numOfMS, blocksToInclude):
    highlights = []

    for run in scoutingData:
        incorrectFieldText = []
        tableHeaderList  = run['blockName'].split(", ")
        
        #loop throught the column headers for each of the tables
        for index, header in enumerate(tableHeaderList):
            
            #make sure that for all tables, the last run number should be equal to the number of cycles the user provided
            if numOfCycles!=run['settings'][-len(tableHeaderList)]:
                incorrectFieldText.append(f"Expected the number of cycles to be {numOfCycles}")
                  
            
            #outlets should be evenly split based on the number of cycles and number of mainstreams
            if "ms_outlet" in header.lower():
                numberToEachOutlet = int(numOfCycles)/int(numOfMS)
                
                outletSettings = run["settings"][index::len(tableHeaderList)]
                runNumber = run["settings"][index-len(tableHeaderList)+1::len(tableHeaderList)]

                for runIndex, val in enumerate(outletSettings):
                    outletVal = "Outlet" + str(math.ceil(int(runNumber[runIndex])/int(numberToEachOutlet)))
                    errorMsg = f"Expected run {runNumber[runIndex]} to go to {outletVal}" 
                    
                    if val!= outletVal and errorMsg not in incorrectFieldText:        
                        incorrectFieldText.append(errorMsg)
                          

            #charge UV should be equal to user input, default is 3.0
            if "charge_wash_uv" in header.lower():
                errorMsg = f"Expected post charge wash UV to be set to {uvPreset}" 
                for val in run["settings"][index::len(tableHeaderList)]:
                    if float(val)!= float(uvPreset) and errorMsg not in incorrectFieldText:        
                        incorrectFieldText.append(errorMsg)
                          

            #post sani rinse should be run after every single step
            if "post" in header.lower() and "sani" in header.lower() and "rinse" in header.lower():
                errorMsg = f"Post Sani Rinse should be run after each step to clear the pump/bubble trap of caustic"
                for val in run["settings"][index::len(tableHeaderList)]:
                    if header.lower() not in val.lower() and errorMsg not in incorrectFieldText:      
                        incorrectFieldText.append(errorMsg)
                          

            #ensure that the flowrates in the scouting section alight with the input from the user
            if "flowrate" in header.lower():
                closestTitleMatch, ratio = closest_match_unit_op(header, pfcData.keys())

                #Pre sani shares a flowrate with equil first cv
                if "first_cv_equil_flowrate" in header.lower():
                    closestTitleMatch = "Pre Sanitization Rinse"
                
                blocksToInclude.remove(closestTitleMatch)

                for key in pfcData.keys():
                    if key == closestTitleMatch :
                        flowRate = pfcData[key]['flow_rate']
                
                for val in run["settings"][index::len(tableHeaderList)]:
                    errorMsg = f"Expected flow rate to be set to {flowRate} for {header}"
                    if float(val)!= float(flowRate) and errorMsg not in incorrectFieldText:        
                        incorrectFieldText.append(errorMsg)
                          


            #Conditions in which only one run is expected to have a certain value, and all other cycles should be blank
            conditions = [
                (["connect_charge_to_inlet_sample"], "Expected only first run to connect charge to inlet sample", 0),
                (["flush", "pre_use", "pause"], "Expected only first run to be turned on for mainstream and filter flushes", 0),
                (["purge"], "Expected only first run to be turned on purges", 0), 
                (["column_storage"], "Column storage should only be turned on for final run", int(numOfCycles)-1)
            ]

            # Iterate over the conditions and call the function for each
            for keywords, errorMsg, cycleIndex in conditions:
                errorList = check_settings(header, run, index, tableHeaderList, keywords, errorMsg, cycleIndex)
                if errorList!=[]:
                    for error in errorList:
                        incorrectFieldText.append(error)

        if incorrectFieldText:
            highlights.append({
                "blockData": run, 
                "annotationText": incorrectFieldText
            })

    for buffer in blocksToInclude:
        if buffer.lower() != "storage" and buffer.lower() != "post sanitization rinse":
            highlights.append({
                "blockData": scoutingData[0], 
                "annotationText": f"Expected a flowrate block for {buffer}"
            })

    return highlights


def check_settings(header, run, index, keyList, keywords, errorMsg, cycleIndex):
    incorrectFieldText = []
    # Check if any of the keywords are in the header
    if any(keyword in header.lower() for keyword in keywords):
        # Iterate over the settings for the current run
        for j, val in enumerate(run["settings"][index::len(keyList)]):
            # Check if the header is not in the value and it's the first run
            if header.lower() not in val.lower() and errorMsg not in incorrectFieldText and j == cycleIndex:
                incorrectFieldText.append(errorMsg)
                  
            # Check if it's not the first run and the value is not "Blank"
            elif j != cycleIndex and "Blank" not in val and errorMsg not in incorrectFieldText:
                incorrectFieldText.append(errorMsg)
    return incorrectFieldText