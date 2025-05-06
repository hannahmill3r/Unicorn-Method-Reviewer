import fitz
import re
import numpy as np
from queryMethodCodeBlocks import queryIndividualBlocks, query_watch, queryFinalBlock

def find_highlight_loc(textDoc, pdf_path, pfcData):

    remainingInlets = list(pfcData.keys())
    # Open PDF document
    doc = fitz.open(pdf_path)
    blocks = textDoc.split("Block: ")
    blockCounter = 1
    firstPurge = True
    purgeBlockData = []
    equillibrationBlockData = []
    individualBlockData = []
    trackedInletQDs = []
    lastPurgeRead = False
    firstBaseRead = False
    finalBlock = {}
    columnParams = {}
    watchBlockData = []
    connection = []

    blockHeaders = []


    # Loop through each page
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Get text with more detailed information including line-level coordinates
        text_instances = page.get_text("dict")["blocks"]
        
        # Loop through text blocks
        for block in text_instances:

            if "lines" in block:  # Check if block contains lines
                for line in block["lines"]:

                    for span in line["spans"]:
                        text = span["text"]
                        
                        #first base contains information on column height and width
                        if "base: " in text.lower() and firstBaseRead == False:
                            #get the location in the PDF of the first Block Line
                            x0 = span["origin"][0]  # Left x coordinate
                            y0 = span["origin"][1]-8  # Top y coordinate
                            x1 = x0 + span["bbox"][2] - span["bbox"][0]  # Right x coordinate
                            y1 = y0 + span["bbox"][3] - span["bbox"][1]  # Bottom y coordinate

                            
                            firstBaseRead = True
                            columnParams = {
                                "blockName": text,
                                "blockPage": page_num+1,
                                "columnData": extractColumnData(text), 
                                "location": (x0, y0, x1, y1)
                            }

                        if "block:" in text.lower() and "purge" in text.lower():


                            #get the location in the PDF of the first Block Line
                            x0 = span["origin"][0]  # Left x coordinate
                            y0 = span["origin"][1]-8  # Top y coordinate
                            x1 = x0 + span["bbox"][2] - span["bbox"][0]  # Right x coordinate
                            y1 = y0 + span["bbox"][3] - span["bbox"][1]  # Bottom y coordinate

                                    
                            blockSettings = queryIndividualBlocks(blocks[blockCounter])
                            if blockSettings !={}:
                                purgeBlockData.append({
                                    "blockName": text,
                                    "blockPage": page_num+1, 
                                    "location": (x0, y0, x1, y1),
                                    "settings": blockSettings,
                                    "First Purge?": firstPurge
                                })

                                trackedInletQDs.append(blockSettings["inlet_QD_setting"])

                                #if we purge an inlet, make sure it is removed from the list of inlets to purge
                                if blockSettings["inlet_setting"] in remainingInlets:
                                    remainingInlets.pop(remainingInlets.index(blockSettings["inlet_setting"]))

                                if "purge_a_pump" not in text.lower() and "purge_a_pump" not in text.lower():
                                    finalPurgeBlock = blockCounter
                                firstPurge = False

                            
                        elif "block:" in text.lower() and "purge" not in text.lower() and firstPurge == False:
                            base_match = re.search(r'Base:\s*(.*)',  blocks[blockCounter])
                            base_value = base_match.group(1).strip().split(', ')[0] if base_match else ' '
                            if re.search('volume', base_value.lower()):
                                lastPurgeRead = True
                            elif re.search('connect', text.lower()) and re.search('inlet', text.lower()):
                                connection.append(extract_connect_info(blocks[blockCounter]))

                        if "block:" in text.lower() and "mainstream" in text.lower():
                            #get the location in the PDF of the first Block Line
                            x0 = span["origin"][0]  # Left x coordinate
                            y0 = span["origin"][1]-8  # Top y coordinate
                            x1 = x0 + span["bbox"][2] - span["bbox"][0]  # Right x coordinate
                            y1 = y0 + span["bbox"][3] - span["bbox"][1]  # Bottom y coordinate

                                    
                            MSBlockSettings = queryIndividualBlocks(blocks[blockCounter])
                            if MSBlockSettings !={}:
                                equillibrationBlockData.append({
                                    "blockName": text,
                                    "blockPage": page_num+1, 
                                    "location": (x0, y0, x1, y1),
                                    "settings": MSBlockSettings
                                })

                        elif "block:" in text.lower() and "watch" in text.lower():
                            x0 = span["origin"][0]  # Left x coordinate
                            y0 = span["origin"][1]-8  # Top y coordinate
                            x1 = x0 + span["bbox"][2] - span["bbox"][0]  # Right x coordinate
                            y1 = y0 + span["bbox"][3] - span["bbox"][1]  # Bottom y coordinate

                                    
                            watchBlockSettings = query_watch(blocks[blockCounter])
                            if watchBlockSettings !={}:
                                watchBlockData = {
                                    "blockName": text,
                                    "blockPage": page_num+1, 
                                    "location": (x0, y0, x1, y1),
                                    "settings": watchBlockSettings
                                }

                            #watch blokcs are indented and their blocks will absorb the snapshot and end settings from the last block, so make that fix here
                            individualBlockData[-1]['settings']['snapshot_setting'] = watchBlockData['settings']['snapshot_setting'][-1]
                            individualBlockData[-1]['settings']['snapshot_breakpoint_setting'] = watchBlockData['settings']['snapshot_breakpoint_setting']
                            individualBlockData[-1]['settings']['end_block_setting'] = watchBlockData['settings']['end_block_setting'][-1]



                        elif "block:" in text.lower() and "purge" not in text.lower():
                            #get the location in the PDF of the first Block Line
                            x0 = span["origin"][0]  # Left x coordinate
                            y0 = span["origin"][1]-8  # Top y coordinate
                            x1 = x0 + span["bbox"][2] - span["bbox"][0]  # Right x coordinate
                            y1 = y0 + span["bbox"][3] - span["bbox"][1]  # Bottom y coordinate

                                    
                            indivBlockSettings = queryIndividualBlocks(blocks[blockCounter])
                            if indivBlockSettings !={}:
                                if "sameasmain" in indivBlockSettings['base_setting'].lower() or "volume" in indivBlockSettings['base_setting'].lower():
                                    individualBlockData.append({
                                        "blockName": text,
                                        "blockPage": page_num+1, 
                                        "location": (x0, y0, x1, y1),
                                        "settings": indivBlockSettings
                                    })
                        #Grab data from last block to check end of run delay and 
                        if "Block: " in text and blockCounter == len(blocks)-1:

                            if queryFinalBlock(blocks[blockCounter])!={}:
                                finalBlock = ({
                                            "blockName": text,
                                            "blockPage": page_num+1, 
                                            "location": (x0, y0, x1, y1),
                                            "settings": queryFinalBlock(blocks[blockCounter])
                                        })
                            scoutingBlock = blocks[blockCounter].split("End_Block")[1]

                            print(parse_scouting_table(scoutingBlock, blockHeaders))
                            
              


                            
                        if "Block: " in text:
                            blockHeaders.append(text)
                            blockCounter+=1

                        
    inletsNotPurged = []
    for val in remainingInlets:
        unpurgedQD = (pfcData.get(val).get('qd')).strip()
        if unpurgedQD != '':
            #we might not purge an inlet if it shares a QD with another purge, so check this first
            if unpurgedQD not in trackedInletQDs:
                inletsNotPurged.append(val)
    doc.close()

    update_inlet_qd_settings(connection, purgeBlockData, equillibrationBlockData)


    return purgeBlockData, inletsNotPurged, equillibrationBlockData, columnParams, individualBlockData, watchBlockData, finalBlock


def extractColumnData(text):
    base = re.search(r'base:\s*(.*)', text.lower())

    columnDiameter = 0
    columnHeight = 0

    base_stripped = base.group(1).strip().split(', ')
    vc = re.sub(r'[A-Za-z]', '', base_stripped[1].split()[0])
    vc = re.sub(r'=', '', vc)


    for param in base_stripped:
        if "_" in param:
            words = param.split("_")
            ind = words.index("x")
            if words[ind-1] =="h":
                columnDiameter = re.sub(r'[A-Za-z]', '', words[ind+1])
                columnHeight = re.sub(r'[A-Za-z]', '', words[ind-2])
            elif words[ind-1] =="d":
                columnDiameter = re.sub(r'[A-Za-z]', '', words[ind-2])
                columnHeight = re.sub(r'[A-Za-z]', '', words[ind+1])
    if columnDiameter == 0:
        return None
    else:
        

        return {
            "columnDiameter": columnDiameter, 
            "columnHeight": columnHeight, 
            "columnVolume": vc
        }
    
def calc_LFlow(columnHeight, columnDiameter, contactTime):
    CSA = (float(columnDiameter)**2*np.pi)/4
    CV =  (columnHeight*CSA)/1000
    volumeOfBuffer = float(CV)*2
    VFlow = (volumeOfBuffer/contactTime)*60
    LFlow = (VFlow/CSA)*1000

    return{
        "columnVolume": CV,
        "linearFlow": LFlow
    }


def extract_connect_info(method_block):
    """
    Analyzes a method block to find connection information and associated QD numbers
    
    Args:
        method_block (str): The UNICORN method block text
    
    Returns:
        dict: Dictionary mapping inlets to their QD numbers
    """
    connections = {}
    
    # Check if block contains "Connect" and "Inlet"
    if "Connect" in method_block and "Inlet" in method_block:
        # Look for QD pattern in the surrounding blocks
        for line in method_block.split('\n'):

                
            # Look for inlet specification    
            if "Connect" in line and "Inlet" in line:
                # Extract inlet name
                inlet = line.split("to")[1].split("and")[0].strip()
                

            if "QD" in line:
                # Extract QD number
                qd_number = line.split("QD")[1].strip().split()[0]
                connections[inlet] = f"QD{qd_number}"
                
    return connections


def update_inlet_qd_settings(connection, purgeBlockData, equillibrationBlockData):
    """
    Updates QD settings for empty inlet settings in purge and equilibration blocks
    
    Args:
        connection (list): List of dictionaries containing inlet to QD mappings
        purgeBlockData (list): List of purge block configurations
        equillibrationBlockData (list): List of equilibration block configurations
    """
    # Process each connection mapping
    for connect in connection:
        # Skip empty connection mappings
        if not connect:
            continue
            
        # For each inlet in the connection mapping
        for inlet, qd_number in connect.items():
            # Update all matching purge blocks that have empty QD settings
            for block in purgeBlockData:
                # Check if inlet matches and QD setting is empty
                if (block['settings']['inlet_setting'] == inlet and 
                    block['settings']['inlet_QD_setting'].strip() == ''):
                    block['settings']['inlet_QD_setting'] = qd_number
                    
            # Update all matching equilibration blocks that have empty QD settings
            for block in equillibrationBlockData:
                # Check if inlet matches and QD setting is empty
                if (block['settings']['inlet_setting'] == inlet and 
                    block['settings']['inlet_QD_setting'].strip() == ''):
                    block['settings']['inlet_QD_setting'] = qd_number


def parse_scouting_table(text, blockHeaders):
    """
    Parse scouting table text with wrapped cell values
    
    Args:
        text (str): The text content of the scouting table
        blockHeaders (list): List of block headers to identify sections in the table
        
    Returns:
        dict: Parsed scouting table data as a dictionary
    """
    try:
        # Split the text into lines
        lines = text.split('\n')
        
        # Initialize variables
        previousHeader = []
        runInfoList = []
        currentHeaderList = []
        nextRun = 1
        recordRunInfo = False
        finalDict = {}
        endEarly = False

        # Iterate through each line in the text
        for line in lines:
            if not endEarly:
                # Check if the line indicates the start of a new run
                if line == "1":
                    recordRunInfo = True

                    #record previous run information, since we are starting a new run
                    if runInfoList != []:
                        finalDict[", ".join(previousHeader)] = runInfoList
                        nextRun = 1

                    runInfoList = []
                    runInfoList.append(line)
                    nextRun += 1

                # Check if the line matches the expected run number
                elif line == str(nextRun):
                    runInfoList.append(line)
                    nextRun += 1
                    recordRunInfo = True

                # If starting a new run, we will need to record the new header information, since runs can go onto multiple, dont overwrite previous headers if its the same as the last one
                elif "run" in line.lower():
                    if previousHeader != currentHeaderList:
                        previousHeader = currentHeaderList

                    currentHeaderList = []
                    recordRunInfo = False
                    currentHeaderList.append(line)

                # method information marks the end of scouting data and the start of operator questions
                elif "method information" in line.lower():
                    endEarly = True
                    finalDict[", ".join(previousHeader)] = runInfoList

                # Record run information if the flag is set
                elif recordRunInfo:
                    runInfoList.append(line)

                # Append to the current header list if not recording run information
                elif not recordRunInfo:
                    currentHeaderList.append(line)

        return finalDict

    except Exception as e:
        # Handle any exceptions that occur during parsing
        print(f"An error occurred while parsing the scouting table: {e}")
        return {}