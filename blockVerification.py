from extractText import closest_match_unit_op
import re
import math
from flowCalculations import calc_LFlow, calc_LFlow_from_residence_time
#from blockNameDict import blockNameDictionary
from blockNameDict_user_validation import *



def check_column_params(methodsColumnParams, pfcColumnParams):
    highlights = []

    methodH = methodsColumnParams["columnData"][ "columnHeight"]
    methodD = methodsColumnParams["columnData"][ "columnDiameter"]
    methodCV = methodsColumnParams["columnData"][ "columnVolume"]

    pfcH = pfcColumnParams['columnHeight']
    pfcD = pfcColumnParams["columnDiameter"]
    pfcContactTime = pfcColumnParams["contactTime"]
    pfcClac = calc_LFlow(pfcH, pfcD, pfcContactTime)

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


def check_purge_block_settings(purge_blocks, pfcData, skid_size, firstPumpAInlet, firstPumpBInlet):
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

    if not firstPumpAInlet:
        firstPumpAInlet = "Inlet 1"
    if not firstPumpBInlet:
        firstPumpBInlet = "Inlet 7"

    
    expected_manflow = skidSizeDict[skid_size]["Manflow"]


    #analyse pump a and b seperately, time based blocks dont have anything we validate so remove them from other purge blocks as well
    #TODO:Check purge pump QD, pump a/b might not be for inlet 1, SHOULD ACTUALLY BE first inlet used from A
    for block in purge_blocks[::-1]:
        incorrectFieldText = []
        if "time" in block['settings']['base_setting'].lower():
            expected_purge_breakpoint = 2.0
        else:
            expected_purge_breakpoint = skidSizeDict[skid_size]["Purge Volume"]
            
        if 'purge_a_pump' in block['blockName'].lower():
            purge_blocks.remove(block)
            for error in validate_common_settings(block['settings'], "Bypass", "Inline", expected_manflow, expected_purge_breakpoint):
                incorrectFieldText.append(error)

            if firstPumpAInlet != block["settings"]['inlet_setting']: 
                incorrectFieldText.append(f"Expected {firstPumpAInlet}")

            if block['settings']['filter_setting']!= "Inline":
                incorrectFieldText.append("Expected inline filter")

        elif 'purge_b_pump' in block['blockName'].lower():
            purge_blocks.remove(block)
            
            for error in validate_common_settings(block['settings'], "Bypass", "Bypass", expected_manflow, expected_purge_breakpoint):
                incorrectFieldText.append(error)
                  
            if firstPumpBInlet != block["settings"]['inlet_setting']: 
                incorrectFieldText.append(f"Expected {firstPumpBInlet}")
                  
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
                    try:
                        if pfcData[key]['qd'].strip() != '' and pfcData[key]['direction'].strip() != '' and pfcData[key]['flow_rate'] != '':
                            pfcQD = pfcData[key]['qd']
                    except:
                        pfcQD = pfcData[key]['qd']


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

        if isinstance(pfcQD, list):
            pfcQD = pfcQD[0]

        if pfcQD != block["settings"]['inlet_QD_setting']:
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
        
        if isinstance(methodQD, list):
            methodQD = methodQD[0]
        if methodQD != block["settings"]['inlet_QD_setting']: 
            blockQD = block["settings"]['inlet_QD_setting']
            incorrectFieldText.append(f"Expected {methodQD}, got {blockQD}")
             
        if incorrectFieldText !=[]:
            highlights.append({
                "blockData": block, 
                "annotationText": incorrectFieldText
            })

    return highlights

def check_indiv_blocks_settings_pdf(indiv_blocks, pfcData, columnParam, userInputCompensationData, skid_size):
    highlights = []
    firstPumpAInlet = None
    firstPumpBInlet = None

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
        for comment in block['settings']['comments_setting']:
            volume = parse_breakpoint_volume(comment, skid_size)
            if volume and isinstance(volume, float):
                expected_flush_breakpoint = volume

        closestTitleMatch, pfcQD, direct, flowRate, residenceTime, columnVolume, pump, inlet, isocraticHoldCV = get_pfc_data_from_block_name(block['blockName'], pfcData)

        #process isocratic hold as a float, if its an empty string, than we will add nothing to the breakpoint value
        if isocraticHoldCV.strip()!='':
            try:
                isocraticHoldCV = float(isocraticHoldCV)
            except:
                isocraticHoldCV = 0
        else:
            isocraticHoldCV = 0

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
            if "A" in pump:
                if not firstPumpAInlet:
                    firstPumpAInlet = inlet
                if ("pa" not in block['settings']['reset_setting'].lower()):

                    #Blocks will sometime's share previous buffer settings if they have the same QD
                    if (indiv_blocks[index-1]['settings']['inlet_QD_setting'] != block['settings']['inlet_QD_setting']) and 'pa' not in indiv_blocks[index-1]['settings']['reset_setting'].lower():
                        incorrectFieldText.append("Totalizer should be reset through pump A")
                          

            #Check buffers that should be reset through wash pump B
            elif "B" in pump:
                if not firstPumpBInlet:
                    firstPumpBInlet = inlet
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
            elif float(block['settings']['end_block_setting'])!= (float(columnVolume) + isocraticHoldCV) and 'flush' not in block['blockName'].lower():
                incorrectFieldText.append(f"Expected {columnVolume} breakpoint volume, got {float(block['settings']['end_block_setting'])}")
          
        except:
            pass
              
        #check the snapshot breakpoint column volumes
        try:
            if 'flush' not in block['blockName'].lower():
                if float(block['settings']['snapshot_breakpoint_setting'])!= (float(columnVolume)+ isocraticHoldCV) and float(block['settings']['snapshot_breakpoint_setting'])!= float(columnVolume):
                    incorrectFieldText.append(f"Expected {columnVolume} breakpoint volume for snapshot")
                      
        except:
           pass     

           '''
        if inlet not in block['settings']['inlet_setting'] or block['settings']['inlet_setting'] not in inlet and inlet.strip()!='' and block['settings']['inlet_setting'].strip()!='':
            #if the previous buffer has the same composition, they will share the same inlet, otherwise, this inlet is incorect
            if indiv_blocks[index-1]['settings']['inlet_setting'] in block['settings']['inlet_setting'] or  block['settings']['inlet_setting'] in indiv_blocks[index-1]['settings']['inlet_setting']:    
                prevClosestTitleMatch, prevPfcQD, prevDirect, prevFlowRate, prevResidenceTime, prevColumnVolume, prevPump, prevInlet, prevIso = get_pfc_data_from_block_name(block['blockName'], pfcData)

                if prevPfcQD not in pfcQD or pfcQD not in prevPfcQD:
                    incorrectFieldText.append(f"Expected {inlet} got {block['settings']['inlet_setting']}")
            else:
                incorrectFieldText.append(f"Expected {inlet} got {block['settings']['inlet_setting']}")
'''
        if incorrectFieldText:
            highlights.append({
                "blockData": block, 
                "annotationText": incorrectFieldText
            })

    return highlights, firstPumpAInlet, firstPumpBInlet

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
            closestTitleMatch, pfcQD, direct, flowRate, residenceTime, columnVolume, pump, inlet, isocraticHoldCV = get_pfc_data_from_block_name(header.lower().strip("flowrate"), pfcData)

            try:
                blocksToInclude.remove(closestTitleMatch)
            except:
                print(closestTitleMatch, " has already been removed")

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
                runNumber = run["settings"][0::len(tableHeaderList)]

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
                    except Exception as e:
                        print("Int value Expected:", val, e)
                          
            #post sani rinse should be run after every single step
            if "post" in header.lower() and "sani" in header.lower() and "rinse" in header.lower():
                errorMsg = f"Post Sani Rinse should be run after each step to clear the pump/bubble trap of caustic"
                for val in run["settings"][index::len(tableHeaderList)]:
                    if header.lower() not in val.lower() and errorMsg not in incorrectFieldText:      
                        incorrectFieldText.append(errorMsg)
                        
                          
            #ensure that the flowrates in the scouting section alight with the input from the user
            if "flow" in header.lower():   
                for val in run["settings"][index::len(tableHeaderList)]:
                    errorMsg = f"Expected flow rate to be set to {flowRate} for {header}"
                    #linearFlow = str(calc_LFlow(columnParam["columnHeight"], columnParam["columnDiameter"], columnParam['contactTime'])["linearFlow"])
                    #residenceFlow = str(calc_LFlow_from_residence_time(columnParam["columnHeight"], residenceTime))
                    try:
                        linearFlow = (calc_LFlow(columnParam["columnHeight"], columnParam["columnDiameter"], columnParam['contactTime'])["linearFlow"])
                        residenceFlow = (calc_LFlow_from_residence_time(columnParam["columnHeight"], residenceTime))
                    except:
                        linearFlow = 0
                        residenceFlow = 0
                    try:
                        if round(float(val))!= round(float(flowRate)) and round(float(val))!= round(linearFlow) and round(float(val)) != round(residenceFlow) and errorMsg not in incorrectFieldText:        
                            incorrectFieldText.append(errorMsg)
                            
                    except Exception as e:
                        print("Int value Expected:", val, tableHeaderList, e, header)

            #Conditions in which only one run is expected to have a certain value, and all other cycles should be blank
            conditions = [
                (["connect_charge_to_inlet_sample"], "Expected only first run to connect charge to inlet sample", 0),
                (["flush", "pre_use_rinse", "pause"], "Expected only first run to be turned on for mainstream and filter flushes", 0),
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
    incorrectFieldText = []
    for buffer in blocksToInclude:
        if buffer != "Storage Rinse":
            incorrectFieldText.append(f"Expected a flowrate block for {buffer}")

    if incorrectFieldText:
            highlights.append({
                "blockData": scoutingData[0], 
                "annotationText": incorrectFieldText
            })

    return highlights


def check_settings(header, run, index, keyList, keywords, errorMsg, cycleIndex):
    incorrectFieldText = []
    # Check if any of the keywords are in the header
    if any(keyword in header.lower() for keyword in keywords):
        # Iterate over the settings for the current run
        for j, val in enumerate(run["settings"][index::len(keyList)]):
            strippedHeader = header.replace('(','').replace(')','').replace('_',' ').replace('#',' ').lower().strip()
            strippedVal = val.replace('(','').replace(')','').replace('_',' ').replace('#',' ').lower().strip()

            # Check if the header is not in the value and it's the first run
            if (strippedHeader not in strippedVal and strippedVal not in strippedHeader)  and errorMsg not in incorrectFieldText and j == cycleIndex:
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
        linearFlow = str(round(calc_LFlow(columnParam["columnHeight"], columnParam["columnDiameter"], columnParam['contactTime'])["linearFlow"]))
        residenceFlow = str(round(calc_LFlow_from_residence_time(columnParam["columnHeight"], residenceTime)))
    except:
        linearFlow = ''
        residenceFlow = ''

    # Validate each flow value
    
    if not any(flow.strip() in flowRate for flow in flows) and not any(flow.strip() in linearFlow for flow in flows) and not any(flow.strip() in residenceFlow for flow in flows) and flowRate.strip() != '':
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

def get_pfc_data_from_block_name(blockName, pfcData):
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

    blockNameDictionary = read_user_valided_blockName()

    closestTitleMatch, ratio = closest_match_unit_op(blockName, blockNameDictionary.keys())
    
    try:
        closestMatchData = pfcData[blockNameDictionary.get(closestTitleMatch)]
        pfcQD = closestMatchData['qd']
        direct = closestMatchData['direction']
        flowRate = closestMatchData['flow_rate']
        residenceTime = closestMatchData['residence time']
        columnVolume = closestMatchData['CV']
        pump = closestMatchData['pump']
        inlet = closestMatchData['inlet']
        isocraticHoldCV = closestMatchData['isocratic hold']

        return blockNameDictionary.get(closestTitleMatch), pfcQD, direct, flowRate, residenceTime, columnVolume, pump, inlet, isocraticHoldCV
    except:
        return '', '', '', '', '', '', '', ''
    

def parse_breakpoint_volume(comment: str, skid_size: str) -> float:
    """
    Parse comments to determine breakpoint volume based on skid size and other parameters
    
    Args:
        comment: The comment text from the method
        skid_size: Size of skid ("3/8", "1/2", or "3/4")
        num_mainstreams: Number of mainstreams (default 1)
    
    Returns:
        Float representing the breakpoint volume in L
    """

    comment = comment.lower()
    
    # Case 1: Fixed volume regardless of skid size
    if "regardless of skid size" in comment and ("breakpoint" in comment.lower() or "block volume" in comment.lower()):
        import re
        volume = float(re.findall(r'(\d+)l', comment)[0])
        return volume
            
        
    # Case 2: Different volumes based on skid size with specific volumes in comment
    if ("breakpoint" in comment.lower() or "block volume" in comment.lower()) and any(size in comment for size in ["3/8", "1/2", "3/4"]):
        import re
        # Extract all number + L patterns
        volumes = re.findall(r'(\d+)l', comment.lower())
        # Extract all size patterns
        sizes = re.findall(r'([134]/[248])"', comment)

        # Create mapping of sizes to volumes
        size_volume_map = {}
        for i, size in enumerate(sizes):
            if i < len(volumes):  # Ensure we have a volume for this size
                if "," in size:  # Handle cases where sizes are combined
                    for sub_size in size.split(","):
                        size_volume_map[sub_size.strip()] = float(volumes[i])
                else:
                    size_volume_map[size] = float(volumes[i])
           
        # Return the volume for the specified skid size
        if skid_size in size_volume_map:
            return size_volume_map[skid_size]
            
        # If we can't find an exact match but sizes are grouped
        if "3/8" in comment and "1/2" in comment and skid_size in ["3/8", "1/2"]:
            # Find volume associated with these sizes
            for i, size in enumerate(sizes):
                if "3/8" in size and "1/2" in size and i < len(volumes):
                    return float(volumes[i])
    
    # Default mappings if no special case matches
    default_volumes = {
        "3/8": 10.0,
        "1/2": 10.0,
        "3/4": 15.0
    }
    return None
