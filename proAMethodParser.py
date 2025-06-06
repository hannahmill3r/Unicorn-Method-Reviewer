import fitz
import re
import numpy as np
from queryMethodCodeBlocks import query_block_data, query_watch, query_final_block, query_column_data
from parseScoutingMethods import parse_scouting_table

"""
Protein A UNICORN Method Parser

Extracts structured data from UNICORN chromatography method PDF files by:
- Parsing block configurations and parameters from method text
- Identifying block locations within the PDF for annotation
- Processing special blocks (purge, equilibration, watch, etc.)
- Extracting column specifications and scouting run data
- Tracking inlet/QD connections and validating purge requirements

Returns a dictionary containing parsed block data, locations, and validation info.
"""

def protein_A_method_parser(textDoc, userInput):

    pdf_path = 'tempfile.pdf'
    pfcData = userInput['inlet_data']


    remainingInlets = list(pfcData.keys())
    # Open PDF document
    doc = fitz.open(pdf_path)
    blocks = textDoc.split("Block: ")
    blockCounter = 1
    firstPurge = True
    firstBaseRead = False
    finalBlock = {}
    columnParams =  {}
    scoutingData ={}
    connection = []
    trackedInletQDs = []
    blockHeaders = []
    scoutingRunLocations = []
    equillibrationBlockData = []
    purgeBlockData = []
    watchBlockData = []
    individualBlockData = []
    allBlockTextExceptLast = ''
    comp_factor_setting = {}
    uvAutoZero = False

    # Loop through each page
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Get text with more detailed information including line-level coordinates
        text_instances = page.get_text("dict")["blocks"]
        
        # Loop through text blocks
        for block in text_instances:

            if "lines" in block:  
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"]
                        
                        #first base contains information on column height and width
                        if "base: " in text.lower() and firstBaseRead == False:                           
                            firstBaseRead = True
                            columnParams = {
                                "blockName": text,
                                "blockPage": page_num+1,
                                "columnData": query_column_data(text), 
                                "location": get_page_location(span)
                            }

                        if "block:" in text.lower() and "purge" in text.lower():

                            blockSettings = query_block_data(blocks[blockCounter])
                            if blockSettings !={}:
                                purgeBlockData.append({
                                    "blockName": text,
                                    "blockPage": page_num+1, 
                                    "location": get_page_location(span),
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
                            MSBlockSettings = query_block_data(blocks[blockCounter])
                            if MSBlockSettings !={}:
                                equillibrationBlockData.append({
                                    "blockName": text,
                                    "blockPage": page_num+1, 
                                    "location": get_page_location(span),
                                    "settings": MSBlockSettings
                                })

                        elif "block:" in text.lower() and "watch" in text.lower():        
                            watchBlockSettings = query_watch(blocks[blockCounter])
                            if watchBlockSettings !={}:
                                watchBlockData.append({
                                    "blockName": text,
                                    "blockPage": page_num+1, 
                                    "location": get_page_location(span),
                                    "settings": watchBlockSettings
                                })

                            #watch blokcs are indented and their blocks will absorb the snapshot and end settings from the last block, so make that fix here
                            if individualBlockData!=[] and watchBlockSettings!=[]:
                                try:
                                    individualBlockData[-1]['settings']['snapshot_setting'] = watchBlockSettings['snapshot_setting'][-1]
                                except (IndexError, KeyError):
                                    individualBlockData[-1]['settings']['snapshot_setting'] = ''
                                
                                try:
                                    individualBlockData[-1]['settings']['snapshot_breakpoint_setting'] = watchBlockSettings['snapshot_breakpoint_setting'][-1]
                                except (IndexError, KeyError):
                                    individualBlockData[-1]['settings']['snapshot_breakpoint_setting'] = ''
                                
                                try:
                                    individualBlockData[-1]['settings']['end_block_setting'] = watchBlockSettings['end_block_setting'][-1]
                                except (IndexError, KeyError):
                                    individualBlockData[-1]['settings']['end_block_setting'] = ''

                        elif "block:" in text.lower() and "purge" not in text.lower():                                   
                            indivBlockSettings = query_block_data(blocks[blockCounter])
                            if indivBlockSettings !={}:
                                if "sameasmain" in indivBlockSettings['base_setting'].lower() or "volume" in indivBlockSettings['base_setting'].lower():
                                    individualBlockData.append({
                                        "blockName": text,
                                        "blockPage": page_num+1, 
                                        "location": get_page_location(span),
                                        "settings": indivBlockSettings
                                    })
                        if "run" in text.lower() and allBlockTextExceptLast!='':                          
                            scoutingRunLocations.append((page_num+1, get_page_location(span)))

                        #Grab data from last block to check end of run delay and 
                        if "Block: " in text and blockCounter == len(blocks)-1:
                            finalBlockData = query_final_block(blocks[blockCounter])

                            if finalBlockData!={}:
                                finalBlock = ({
                                            "blockName": text,
                                            "blockPage": page_num+1, 
                                            "location": get_page_location(span),
                                            "settings": finalBlockData
                                        })
                            scoutingBlock = blocks[blockCounter].split("End_Block")[1]

                            allBlockTextExceptLast = '/n'.join(blocks[0:blockCounter-1])

                        #uv auto zero needs to be present in every run
                        if "uv" in text.lower() and "auto" in text.lower() and "zero" in text.lower():
                            uvAutoZero = True
                        
                        if "Block: " in text:
                            blockHeaders.append(text)
                            blockCounter+=1


    scoutingData = (parse_scouting_table(scoutingBlock, allBlockTextExceptLast, scoutingRunLocations))

    inletsNotPurged = []
    for val in remainingInlets:
        unpurgedQD = (pfcData.get(val).get('qd'))
        if isinstance(unpurgedQD, list):
            for qd in unpurgedQD:
                qd.strip()
                if qd.strip() != ''and qd.strip() not in trackedInletQDs:
                    inletsNotPurged.append(val)
        elif unpurgedQD.strip() != ''and unpurgedQD.strip() not in trackedInletQDs:
                inletsNotPurged.append(val)
    doc.close()

    #purge and equil blocks might have empty inlet settings if they chare an inlet, so fill in any missing data with shared inlet connections
    update_inlet_qd_settings(connection, purgeBlockData, equillibrationBlockData)


    return {
        "purge_data": purgeBlockData, 
        "inlets_not_purged": inletsNotPurged, 
        "equilibration_data": equillibrationBlockData, 
        "column_params": columnParams, 
        "indiv_block_data": individualBlockData, 
        "watch_block_data": watchBlockData, 
        "final_block_data": finalBlock, 
        "scouting_data": scoutingData, 
        "compensation_factor": comp_factor_setting, 
        "UV_Auto_Zero": uvAutoZero
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
                if (block['settings']['inlet_setting'] == inlet and block['settings']['inlet_QD_setting'].strip() == ''):
                    block['settings']['inlet_QD_setting'] = qd_number
                    
            # Update all matching equilibration blocks that have empty QD settings
            for block in equillibrationBlockData:
                # Check if inlet matches and QD setting is empty
                if (block['settings']['inlet_setting'] == inlet and block['settings']['inlet_QD_setting'].strip() == ''):
                    block['settings']['inlet_QD_setting'] = qd_number


def get_page_location(span):
    """
    Extracts the page location from the span object
    
    Args:
        span fitz object: contains text and location data within a pdf
    """

    x0 = span["origin"][0]  # Left x coordinate
    y0 = span["origin"][1]-8  # Top y coordinate
    x1 = x0 + span["bbox"][2] - span["bbox"][0]  # Right x coordinate
    y1 = y0 + span["bbox"][3] - span["bbox"][1]  # Bottom y coordinate

    return (x0, y0, x1, y1)