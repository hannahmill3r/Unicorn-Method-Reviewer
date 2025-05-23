from extractText import closest_match_unit_op
import re
import math
from flowCalculations import calc_LFlow, calc_LFlow_from_residence_time

"""
Block Verification

This script validates chromatography method blocks against defined requirements by:
- Checking column parameters (height, diameter, volume)
- Validating purge, mainstream, and individual block settings
- Verifying correct flow rates, residence times, and outlet configurations
- Ensuring proper watch settings for UV monitoring and peak collection
- Confirming scouting run parameters match PFC specifications

The functions defined in the script all return highlight annotations, including pdf location and text
for any validation failures.
"""

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


def check_purge_block_settings(purge_blocks, pfcData, skid_size):
    """
    Check purge method block data against the user entered pfc data 
    
    Args:
        purge_blocks (dict): Contains all relevant data to the code block, such as name, manflow, linear flow rate, etc.
        pfcData (dict): Contains all pfc input data from the user for all inlets, (equil, charge, post sani, etc.)
        
    Returns:
        highlights (dict): list of highlight block dictionary and the error messages associated with the block
    """
        
    highlights = []

    skidSizeDict = {
        '3/8': {"Manflow": 100, "Purge Volume": 7},
        '1/2': {"Manflow": 100, "Purge Volume": 10},
        '3/4': {"Manflow": 60, "Purge Volume": 15}
    }

    
    expected_manflow = skidSizeDict[skid_size]["Manflow"]


    #analyse pump a and b seperately, time based blocks dont have anything we validate so remove them from other purge blocks as well
    for block in purge_blocks[::-1]:
        incorrectFieldText = []
        if "time" in block['settings']['base_setting'].lower():
            expected_purge_breakpoint = 2.0
        else:
            expected_purge_breakpoint = skidSizeDict[skid_size]["Purge Volume"]
            
        if 'purge_a_pump' in block['blockName'].lower():
            purge_blocks.remove(block)
            #TODO: the breakpoint volume is hard coded and needs to be extracted based on the sharepoint file linked
            for error in validate_common_settings(block['settings'], "Bypass", "Inline", expected_manflow, expected_purge_breakpoint):
                incorrectFieldText.append(error)

            if "Inlet 1" != block["settings"]['inlet_setting']: 
                incorrectFieldText.append(f"Expected Inlet 1")

            if block['settings']['filter_setting']!= "Inline":
                incorrectFieldText.append("Expected inline filter")

        elif 'purge_b_pump' in block['blockName'].lower():
            purge_blocks.remove(block)
            
            for error in validate_common_settings(block['settings'], "Bypass", "Bypass", expected_manflow, expected_purge_breakpoint):
                incorrectFieldText.append(error)
                  
            if "Inlet 7" != block["settings"]['inlet_setting']: 
                incorrectFieldText.append(f"Expected Inlet 7")
                  
            if block['settings']['filter_setting']!= "Bypass":
                incorrectFieldText.append("Expected bypass filter")
                          
        elif re.search('time', block['settings']['base_setting'].lower()):
            purge_blocks.remove(block)

        if incorrectFieldText:
            highlights.append({
                "blockData": block, 
                "annotationText": incorrectFieldText
            })
     
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
        if blockCounter ==0:
            for error in validate_common_settings(block['settings'], "downflow, upflow", "Bypass", expected_manflow, int(expected_purge_breakpoint)*2):
                incorrectFieldText.append(error)

        #Check all other settings, all inlets should be set to bypass and waste. Manflow and QD setting should match pfc provided information
        elif blockCounter!= len(purge_blocks)-1:
            for error in validate_common_settings(block['settings'], "Bypass", "Bypass", expected_manflow, int(expected_purge_breakpoint)):
                incorrectFieldText.append(error)

        else:
            for error in validate_common_settings(block['settings'], "Bypass", "Inline", expected_manflow, float(20.0)):
                incorrectFieldText.append(error)
    
            if pfcData['Equilibration']['qd']!= pfcQD != block["settings"]['inlet_QD_setting']:
                incorrectFieldText.append(f"Final purge should use equillibration buffer")

        if  pfcQD != block["settings"]['inlet_QD_setting']:
            incorrectFieldText.append(f"Expected {pfcQD}")
        
        if incorrectFieldText:
            highlights.append({
                "blockData": block, 
                "annotationText": incorrectFieldText
            })

    return highlights


def check_MS_blocks_settings_pdf(MS_blocks, pfcData, numberofMS, skid_size):
    highlights = []


    skidSizeDict = {
        '3/8': {"Manflow": 100, "Purge Volume": 7},
        '1/2': {"Manflow": 100, "Purge Volume": 10},
        '3/4': {"Manflow": 60, "Purge Volume": 15}
    }

    expected_manflow = skidSizeDict[skid_size]["Manflow"]


    for block in MS_blocks:

        incorrectFieldText = []
        methodQD = pfcData['Equilibration']['qd']

        for error in validate_common_settings(block['settings'],  "Bypass", "Inline", expected_manflow, float(numberofMS)*5):
                incorrectFieldText.append(error)
   
        if "Inline" not in block["settings"]['filter_setting']:
            incorrectFieldText.append("Expected Inline filter")
       
        if int(block["settings"]['fraction_setting']) != int(numberofMS):
            incorrectFieldText.append(f"Expected number of mainstreams to be: {numberofMS}")
            
        if methodQD != block["settings"]['inlet_QD_setting']: 
            incorrectFieldText.append(f"Expected {methodQD}")
             
        if incorrectFieldText !=[]:
            highlights.append({
                "blockData": block, 
                "annotationText": incorrectFieldText
            })

    return highlights

def check_indiv_blocks_settings_pdf(indiv_blocks, pfcData, columnParam, userInputCompensationData, skid_size):
    highlights = []

    skidSizeDict = {
        '3/8': {"Manflow": 100, "Purge Volume": 7},
        '1/2': {"Manflow": 100, "Purge Volume": 10},
        '3/4': {"Manflow": 60, "Purge Volume": 15}
    }

    expected_flush_breakpoint = skidSizeDict[skid_size]["Purge Volume"]
    expected_manflow = skidSizeDict[skid_size]["Manflow"]

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

        if "Inline" not in block["settings"]['filter_setting']:
            incorrectFieldText.append("Expected Inline filter")
              
        if "Inline" not in block["settings"]['bubbletrap_setting']:
            incorrectFieldText.append("Expected bubbletrap bypass")
              

        #all outlets go to wast EXCEPT for elution
        if "waste" not in block["settings"]['outlet_setting'].lower() and "watch_uv" not in block['blockName'].lower():
            incorrectFieldText.append("Expected waste outlet")
        
        for error in (validate_flow_settings(block, equilLFlow, flowRate, columnParam, residenceTime, pfcData)):
            incorrectFieldText.append(error)

        if "flush" in block["blockName"].lower():
            match, ratio = closest_match_unit_op(block['settings']['setmark_setting'], [block["blockName"]])
            if ratio < .20:
                incorrectFieldText.append("Please double check setmark naming, similarity score was low")
            if "Bypass" not in block["settings"]['column_setting']:
                incorrectFieldText.append(f"Expected Bypass")
            if block["settings"]['manflow'] != ' ' and block["settings"]['manflow'] != expected_manflow:
                incorrectFieldText.append(f"Expected {expected_manflow}% manflow, got ", block["settings"]['manflow'])
        
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

            if not any(term in block["blockName"] for term in block['settings']['setmark_setting'].split()) and not any(term in block["blockName"] for term in block['settings']['setmark_setting'].split('_')) and block['settings']['setmark_setting'].strip() !='':
                incorrectFieldText.append("Incorrect setmark naming")
            if direct.strip() != '' and direct.lower() not in block["settings"]['column_setting'].lower():
                incorrectFieldText.append(f"Expected {direct}")

        try:
            if float(block['settings']['compensation_setting'])!= float(userInputCompensationData):
                incorrectFieldText.append(f"Expected compensation factor to be {userInputCompensationData}")
        except:
            pass
        
        
        if not any(term in block["blockName"] for term in block['settings']['snapshot_setting'].split()) and not any(term in block["blockName"] for term in block['settings']['snapshot_setting'].split('_'))and block['settings']['snapshot_setting'].strip() !='':
            incorrectFieldText.append("Incorrect snapshot naming")      


        
                  
        #check the end block breakpoint column volumes
        try:
            if 'flush' in block['blockName'].lower() and float(block['settings']['end_block_setting'])!= float(expected_flush_breakpoint):
                incorrectFieldText.append(f"Expected flush to have {float(expected_flush_breakpoint)} breakpoint volume, got {str(block['settings']['end_block_setting'])}")
            elif float(block['settings']['end_block_setting'])!= float(CV) and 'flush' not in block['blockName'].lower():
                incorrectFieldText.append(f"Expected {CV} breakpoint volume, got {float(block['settings']['end_block_setting'])}")
          
        except:
            incorrectFieldText.append(f"I was unable to process the formatting for the breakpoint volume, please double check it")
              
        #check the snapshot breakpoint column volumes
        try:
            if 'flush' not in block['blockName'].lower():
                if float(block['settings']['snapshot_breakpoint_setting'])!= float(CV):
                    incorrectFieldText.append(f"Expected {CV} breakpoint volume for snapshot")
                    #print(CV, block['settings']['snapshot_breakpoint_setting'], block['blockName'].lower(), closesTagMatch)
                      
        except:
            incorrectFieldText.append(f"I was unable to process the formatting for the snapshot breakpoint volume, please double check it")
              
        #TODO: check inlets?

        if incorrectFieldText:
            highlights.append({
                "blockData": block, 
                "annotationText": incorrectFieldText
            })

    return highlights

def check_watch_settings(blocks):

    highlights = []
    

    for block in blocks:
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
        
def check_scouting(scoutingData, pfcData, uvPreset, numOfCycles, numOfMS, blocksToInclude, columnParam):
    highlights = []

    for run in scoutingData:
        incorrectFieldText = []
        tableHeaderList  = run['blockName'].split(", ")
        
        #loop throught the column headers for each of the tables
        for index, header in enumerate(tableHeaderList):

            numCyclesError = f"Expected the number of cycles to be {numOfCycles}"
            
            #make sure that for all tables, the last run number should be equal to the number of cycles the user provided
            if numOfCycles!=run['settings'][-len(tableHeaderList)] and numCyclesError not in incorrectFieldText:
                incorrectFieldText.append(f"Expected the number of cycles to be {numOfCycles}")
                  
            
            #outlets should be evenly split based on the number of cycles and number of mainstreams
            if "ms_outlet" in header.lower():
                try:
                    numberToEachOutlet = int(numOfCycles)/int(numOfMS)
                except:
                    numberToEachOutlet = 1
                
                outletSettings = run["settings"][index::len(tableHeaderList)]
                #runNumber = run["settings"][index-len(tableHeaderList)+1::len(tableHeaderList)]
                runNumber = run["settings"][0::len(tableHeaderList)]
                #print("INDEX", tableHeaderList, index, index-len(tableHeaderList)+1, runNumber, outletSettings, run["settings"])

                for runIndex, val in enumerate(outletSettings):
                    try:
                        outletVal = "Outlet" + str(math.ceil(int(runNumber[runIndex])/int(numberToEachOutlet)))
                        errorMsg = f"Expected run {runNumber[runIndex]} to go to {outletVal}" 
                    
                    
                        if val!= outletVal and errorMsg not in incorrectFieldText:        
                            incorrectFieldText.append(errorMsg)
                    except:
                        print("error processing run index: ", runNumber, runIndex)
                          
            #charge UV should be equal to user input, default is 3.0
            if "charge_wash_uv" in header.lower():
                errorMsg = f"Expected post charge wash UV to be set to {uvPreset}" 
                for val in run["settings"][index::len(tableHeaderList)]:
                    try:
                        if float(val)!= float(uvPreset) and errorMsg not in incorrectFieldText:        
                            incorrectFieldText.append(errorMsg)
                    except:
                        print("Int value Expected:", val)
                          
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
                
                try:
                    blocksToInclude.remove(closestTitleMatch)
                except:
                    print(closestTitleMatch, " has already been removed")

                for key in pfcData.keys():
                    if key == closestTitleMatch :
                        flowRate = pfcData[key]['flow_rate']
                        residenceTime = pfcData[key]['residence time']
                
                for val in run["settings"][index::len(tableHeaderList)]:
                    errorMsg = f"Expected flow rate to be set to {flowRate} for {header}"
                    linearFlow = str(calc_LFlow(columnParam["columnHeight"], columnParam["columnDiameter"], columnParam['contactTime'])["linearFlow"])
                    residenceFlow = str(calc_LFlow_from_residence_time(columnParam["columnHeight"], residenceTime))
                    try:
                        linearFlow = (calc_LFlow(columnParam["columnHeight"], columnParam["columnDiameter"], columnParam['contactTime'])["linearFlow"])
                        residenceFlow = (calc_LFlow_from_residence_time(columnParam["columnHeight"], residenceTime))
                    except:
                        linearFlow = 0
                        residenceFlow = 0
                    try:

                        if float(val)!= float(flowRate) and float(val)!= linearFlow and float(val) != residenceFlow and errorMsg not in incorrectFieldText:        
                            incorrectFieldText.append(errorMsg)
                    except:
                        print("Int value Expected:", val, tableHeaderList)

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


def validate_flow_settings(block, equilLFlow, flowRate, columnParam, residenceTime, pfcData):
            """
            Validates flow rate settings against expected values for different block types
            Args:
                block: Current method block being validated
                equilLFlow: Expected equilibration/sanitization flow rate
                flowRate: Standard flow rate from PFC
                columnParam: Column parameters (height, etc)
                residenceTime: Expected residence time
                pfcData: Process data containing expected values
            """
            incorrectFieldText = []
            
            # Get flow settings and tags
            flows = [block['settings']['flow_setting']] 
            
            # Split into lists if multiple flows specified
            if "," in block['settings']['flow_setting']:
                flows = block['settings']['flow_setting'].strip().split(",")
            try:
                linearFlow = str(calc_LFlow(columnParam["columnHeight"], columnParam["columnDiameter"], columnParam['contactTime'])["linearFlow"])
                residenceFlow = str(calc_LFlow_from_residence_time(columnParam["columnHeight"], residenceTime))
            except:
                linearFlow = ''
                residenceFlow = ''

            # Validate each flow value
            if not any(flow in flowRate for flow in flows) and not any(flow in linearFlow for flow in flows) and not any(flow in residenceFlow for flow in flows):
                incorrectFieldText.append(f"Expected {flowRate} flow")

            return incorrectFieldText


def validate_common_settings(block_settings, column, bubbletrap, manflow, breckpoint_volume):
    """
    Validates block settings against common check dictionary
    
    Args:
        block_settings (dict): Dictionary containing block settings to validate
        common_checks (dict): Dictionary of expected values and error messages
        
    Returns:
        list: List of error messages for failed validations
    """


    common_checks = {
        'manflow': (manflow, f"Expected {manflow}% ManFlow"),
        'outlet_setting': ('Waste', "All purges should go to waste"),
        #'base_setting': (base, "Expected pump purge to be in time"), 
        'bubbletrap_setting': (bubbletrap, f"Expected bubbletrap: {bubbletrap}"),
        'column_setting': (column, f"Expected column: {column}"), 
        'end_block_setting': (breckpoint_volume, f"Expected breakpoint volume: {breckpoint_volume}")
    }
    errors = []
    
    for setting, (expected_value, error_msg) in common_checks.items():
        if ', ' in str(expected_value):
            for i in expected_value.split(", "):
                if str(i).strip().lower() not in str(block_settings[setting]).lower():
                    errors.append(error_msg)

        elif str(expected_value).lower() not in str(block_settings[setting]).lower() and str(block_settings[setting]).strip()!='':
            errors.append(error_msg)

    return errors