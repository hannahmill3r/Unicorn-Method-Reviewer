import fitz
import re

def find_highlight_loc(textDoc, pdf_path, pfcData):

    remainingInlets = list(pfcData.keys())
    # Open PDF document
    doc = fitz.open(pdf_path)
    blocks = textDoc.split("Block: ")
    blockCounter = 1
    firstPurge = True
    purgeBlockData = []
    equillibrationBlockData = []
    trackedInletQDs = []
    lastPurgeRead = False

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
                        if "block:" in text.lower() and "purge" in text.lower() and not lastPurgeRead:


                            #get the location in the PDF of the first Block Line
                            x0 = span["origin"][0]  # Left x coordinate
                            y0 = span["origin"][1]-8  # Top y coordinate
                            x1 = x0 + span["bbox"][2] - span["bbox"][0]  # Right x coordinate
                            y1 = y0 + span["bbox"][3] - span["bbox"][1]  # Bottom y coordinate

                                    
                            blockSettings = queryPurgeBlock(blocks[blockCounter])
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

                                finalPurgeBlock = blockCounter
                                firstPurge = False

                            
                        elif "block:" in text.lower() and "purge" not in text.lower() and firstPurge == False:
                            base_match = re.search(r'Base:\s*(.*)',  blocks[blockCounter])
                            base_value = base_match.group(1).strip().split(', ')[0] if base_match else ' '
                            if re.search('volume', base_value.lower()):
                                lastPurgeRead = True

                        if "block:" in text.lower() and "mainstream" in text.lower():
                            #get the location in the PDF of the first Block Line
                            x0 = span["origin"][0]  # Left x coordinate
                            y0 = span["origin"][1]-8  # Top y coordinate
                            x1 = x0 + span["bbox"][2] - span["bbox"][0]  # Right x coordinate
                            y1 = y0 + span["bbox"][3] - span["bbox"][1]  # Bottom y coordinate

                                    
                            MSBlockSettings = queryMainstreamBlock(blocks[blockCounter])
                            if MSBlockSettings !={}:
                                equillibrationBlockData.append({
                                    "blockName": text,
                                    "blockPage": page_num+1, 
                                    "location": (x0, y0, x1, y1),
                                    "settings": MSBlockSettings
                                })



                        if "Block: " in text:
                            blockCounter+=1

                        
    inletsNotPurged = []
    for val in remainingInlets:
        unpurgedQD = (pfcData.get(val).get('qd')).strip()
        if unpurgedQD != '':
            #we might not purge na inlet if it shares a QD with another purge, so check this first
            if unpurgedQD not in trackedInletQDs:
                inletsNotPurged.append(val)
    doc.close()
    return purgeBlockData, inletsNotPurged, equillibrationBlockData


def queryMainstreamBlock(block):
    # Find matches and store their locations
    currentPurgeBlock = {}
    manflow_match = re.search(r'ManFlow:\s*(\d+\.?\d*)\s*{\%}', block)
    column_match = re.search(r'Column:\s*(.*)', block)
    filter_match = re.search(r'Filter:\s*(.*)', block)
    fraction_match = re.search(r'Fractions:\s*(.*)', block)
    outlet_match = re.search(r'Outlet:\s*(.*)', block)
    bubbletrap_match = re.search(r'BubbleTrap:\s*(.*)', block)
    QD_match = re.search(r'QD\s*(.*)', block)
    base_match = re.search(r'Base:\s*(.*)', block)
    end_block_match = re.search(r'(\d+\.?\d*)\s*End_Block', block)
    inlet_match = re.search(r'Inlet:\s*(.*)', block)


    base_value = base_match.group(1).strip().split(', ')[0] if base_match else ' '
    end_block_value = float(end_block_match.group(1)) if end_block_match else ' '
    flow_value = float(manflow_match.group(1)) if manflow_match else ' '
    column_setting = column_match.group(1).strip() if column_match else ' '
    outlet_setting = outlet_match.group(1).strip() if outlet_match else ' '
    bubbletrap_setting = bubbletrap_match.group(1).strip() if bubbletrap_match else ' '
    filter_setting = filter_match.group(1).strip() if filter_match else ' '
    QD_match_value = QD_match.group().strip().replace(" ", "") if QD_match else ' '

    numberOfMS = 0
    if fraction_match:
        fraction_spec = fraction_match.group(1).strip()
        numberOfMS = fraction_spec.split(',')[0]



    if re.search('volume', base_value.lower()):

        inlet_number = None
        if inlet_match:
            inlet_spec = inlet_match.group(1).strip()
            for part in inlet_spec.split(','):
                part = part.strip()
                if 'Inlet' in part and part != 'Inlet':
                    inlet_number = ''.join(filter(str.isdigit, part))
                    inlet_setting = 'Inlet'+inlet_number
                elif 'Sample' in part:
                    inlet_number = 'Sample'
                    inlet_setting = 'Sample'

            currentMSBlock = {
                'manflow': flow_value,
                'column_setting': column_setting,
                'outlet_setting': outlet_setting,
                'bubbletrap_setting': bubbletrap_setting,
                'inlet_QD_setting': QD_match_value,
                'inlet_setting': inlet_setting,
                'end_block_setting': end_block_value, 
                'filter_setting': filter_setting, 
                'fraction_setting': numberOfMS
            }
    return currentMSBlock


def check_MS_blocks_settings_pdf(MS_blocks, pfcData):
    highlights = []
    incorrectField = False
    firstBlock = True

    #TODO: change this to read in the campaign planner or take user input
    numberofMSFromCampaignPlanner = 3

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
            incorrectFieldText.append("Expected final volume to be 5L")
            incorrectField = True
        if int(block["settings"]['fraction_setting']) != numberofMSFromCampaignPlanner:
            incorrectFieldText.append(f"Expected number of mainstreams to be:")
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



def queryPurgeBlock(block):
    # Find matches and store their locations
    currentPurgeBlock = {}
    manflow_match = re.search(r'ManFlow:\s*(\d+\.?\d*)\s*{\%}', block)
    column_match = re.search(r'Column:\s*(.*)', block)
    outlet_match = re.search(r'Outlet:\s*(.*)', block)
    bubbletrap_match = re.search(r'BubbleTrap:\s*(.*)', block)
    QD_match = re.search(r'QD\s*(.*)', block)
    base_match = re.search(r'Base:\s*(.*)', block)
    end_block_match = re.search(r'(\d+\.?\d*)\s*End_Block', block)
    inlet_match = re.search(r'Inlet:\s*(.*)', block)

    multi_column_math = re.finditer(r'Column:\s*(.*)', block)
    columnMatches = []
    for match in multi_column_math:
        columnMatches.append(match.group(1).strip())

    base_value = base_match.group(1).strip().split(', ')[0] if base_match else ' '
    end_block_value = float(end_block_match.group(1)) if end_block_match else ' '
    flow_value = float(manflow_match.group(1)) if manflow_match else ' '
    column_setting = column_match.group(1).strip() if column_match else ' '
    outlet_setting = outlet_match.group(1).strip() if outlet_match else ' '
    bubbletrap_setting = bubbletrap_match.group(1).strip() if bubbletrap_match else ' '
    QD_match_value = QD_match.group().strip().replace(" ", "") if QD_match else ' '

    #if theres more than one, return string listing all matches. This should only be applicable in the first purge
    if len(columnMatches)>1:
        column_setting = ', '.join(columnMatches)

    if re.search('volume', base_value.lower()):

        inlet_number = None
        if inlet_match:
            inlet_spec = inlet_match.group(1).strip()
            for part in inlet_spec.split(','):
                part = part.strip()
                if 'Inlet' in part and part != 'Inlet':
                    inlet_number = ''.join(filter(str.isdigit, part))
                    inlet_setting = 'Inlet'+inlet_number
                elif 'Sample' in part:
                    inlet_number = 'Sample'
                    inlet_setting = 'Sample'

            currentPurgeBlock = {
                'manflow': flow_value,
                'column_setting': column_setting,
                'outlet_setting': outlet_setting,
                'bubbletrap_setting': bubbletrap_setting,
                'inlet_QD_setting': QD_match_value,
                'inlet_setting': inlet_setting,
                'end_block_setting': end_block_value
            }
    return currentPurgeBlock


def check_purge_blocks_settings_pdf2(purge_blocks, pfcData):
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




