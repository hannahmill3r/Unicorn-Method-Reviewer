import fitz

def check_purge_blocks_settings_from_pdf(pdf):

    doc = fitz.open(pdf)
    
    # Loop through each page
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Get text blocks from page
        text_blocks = page.get_text("blocks")
        
        # Loop through text blocks
        for block in text_blocks:
            text = block[4]  # Text content is in index 4
            location = block[:4]  # Location coordinates are in indices 0-3
            
            # Check each line for "manflow" (case insensitive)
            for line in text.split('\n'):
                if 'manflow' in line.lower():
                    print(f"Page {page_num + 1}")
                    print(f"Text: {line.strip()}")
                    print(f"Location: x0={location[0]}, y0={location[1]}, x1={location[2]}, y1={location[3]}")
                    print("-" * 50)
    
    doc.close()



    '''
    blocks = text.split("Block: ")
    remainingInlets = list(pfcData.keys())
    purge_blocks = []
    current_position = 0  # Track position in text

    for block in blocks:
        block_start = current_position + len("Block: ")  # Account for the split text
        first_line = block.split('\n')[0] if block else ''
        firstBlockAfterPurge = False
        finalPurgeBlock = None
        lastPurgeBuffer = False
        firstPurgeEntered = False
        locations = {}  # Store match locations

        if 'Purge' in first_line:
            firstPurgeEntered = True

            # Store the location of the first line of the purge block
            first_line_location = {
                'start': block_start,
                'end': block_start + len(first_line),
                'line': text[:block_start].count('\n') + 1,
                'text': first_line
            }
            
            locations = {'block_start': first_line_location}
            
            # Find matches and store their locations
            manflow_match = re.search(r'ManFlow:\s*(\d+\.?\d*)\s*{\%}', block)
            if manflow_match:
                locations['manflow'] = {
                    'start': block_start + manflow_match.start(),
                    'end': block_start + manflow_match.end(),
                    'line': text[:block_start + manflow_match.start()].count('\n') + 1,
                    'text': manflow_match.group()
                }
            else:
                locations['manflow'] = first_line_location

            column_match = re.search(r'Column:\s*(.*)', block)
            if column_match:
                locations['column'] = {
                    'start': block_start + column_match.start(),
                    'end': block_start + column_match.end(),
                    'line': text[:block_start + column_match.start()].count('\n') + 1,
                    'text': column_match.group()
                }
            else:
                locations['column'] = first_line_location

            outlet_match = re.search(r'Outlet:\s*(.*)', block)
            if outlet_match:
                locations['outlet'] = {
                    'start': block_start + outlet_match.start(),
                    'end': block_start + outlet_match.end(),
                    'line': text[:block_start + outlet_match.start()].count('\n') + 1,
                    'text': outlet_match.group()
                }
            else:
                locations['outlet'] = first_line_location

            bubbletrap_match = re.search(r'BubbleTrap:\s*(.*)', block)
            if bubbletrap_match:
                locations['bubbletrap'] = {
                    'start': block_start + bubbletrap_match.start(),
                    'end': block_start + bubbletrap_match.end(),
                    'line': text[:block_start + bubbletrap_match.start()].count('\n') + 1,
                    'text': bubbletrap_match.group()
                }
            else:
                locations['bubbletrap'] = first_line_location

            QD_match = re.search(r'QD\s*(.*)', block)
            if QD_match:
                locations['QD'] = {
                    'start': block_start + QD_match.start(),
                    'end': block_start + QD_match.end(),
                    'line': text[:block_start + QD_match.start()].count('\n') + 1,
                    'text': QD_match.group()
                }
            else:
                locations['QD'] = first_line_location

            base_match = re.search(r'Base:\s*(.*)', block)
            if base_match:
                locations['base'] = {
                    'start': block_start + base_match.start(),
                    'end': block_start + base_match.end(),
                    'line': text[:block_start + base_match.start()].count('\n') + 1,
                    'text': base_match.group()
                }
            else:
                locations['base'] = first_line_location

            end_block_match = re.search(r'(\d+\.?\d*)\s*End_Block', block)
            if end_block_match:
                locations['endBlock'] = {
                    'start': block_start + end_block_match.start(),
                    'end': block_start + end_block_match.end(),
                    'line': text[:block_start + end_block_match.start()].count('\n') + 1,
                    'text': end_block_match.group()
                }
            else:
                locations['endBlock'] = first_line_location


            inlet_match = re.search(r'Inlet:\s*(.*)', block)
            if inlet_match:
                locations['inlet'] = {
                    'start': block_start + inlet_match.start(),
                    'end': block_start + inlet_match.end(),
                    'line': text[:block_start + inlet_match.start()].count('\n') + 1,
                    'text': inlet_match.group()
                }
            else:
                locations['inlet'] = first_line_location

            base_value = base_match.group(1).strip().split(', ')[0] if base_match else ' '
            end_block_value = float(end_block_match.group(1)) if end_block_match else ' '
            flow_value = float(manflow_match.group(1)) if manflow_match else ' '
            column_setting = column_match.group(1).strip() if column_match else ' '
            outlet_setting = outlet_match.group(1).strip() if outlet_match else ' '
            bubbletrap_setting = bubbletrap_match.group(1).strip() if bubbletrap_match else ' '
            QD_match_value = QD_match.group().strip().replace(" ", "") if QD_match else ' '

            if re.search('volume', base_value.lower()):
                block_name = first_line.strip()
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
                        'block_name': block_name,
                        'manflow': flow_value,
                        'column_setting': column_setting,
                        'outlet_setting': outlet_setting,
                        'bubbletrap_setting': bubbletrap_setting,
                        'inlet_QD_setting': QD_match_value,
                        'inlet_setting': inlet_setting,
                        'end_block_setting': end_block_value,
                        'locations': locations  # Include match locations
                    }

                    purge_blocks.append(currentPurgeBlock)
                    finalPurgeBlock = currentPurgeBlock

                    if inlet_setting in remainingInlets:
                        remainingInlets.pop(remainingInlets.index(inlet_setting))

        elif firstPurgeEntered and not firstBlockAfterPurge:
            if finalPurgeBlock is not None:
                inlet_match = re.search(r'Inlet:\s*(.*)', block)
                inlet_match = inlet_match.group(1).strip()
                if (finalPurgeBlock['inlet_setting'] in inlet_match):
                    lastPurgeBuffer = True

        current_position += len(block) + len("Block: ")  # Update position for next block

    if not purge_blocks:
        return [], False, False, False, []

    standard_settings_correct = all(
        block['manflow'] == 60.0 and 
        ('Bypass_Both' in block['column_setting'] or 'Bypass' in block['column_setting']) and
        block['outlet_setting'] == 'Waste' and
        block['bubbletrap_setting'] == 'Bypass' and 
        pfcData.get(block['inlet_setting']).get('qd') == block['inlet_QD_setting']
        for block in purge_blocks[:-1]
    )
    
    last_purge_correct = (
        purge_blocks[-1]['manflow'] == 60.0 and 
        ('Bypass_Both' in purge_blocks[-1]['column_setting'] or 'Bypass' in purge_blocks[-1]['column_setting']) and
        'Waste' in purge_blocks[-1]['outlet_setting'] and 
        20.0 == purge_blocks[-1]['end_block_setting'] and
        'Inline' in purge_blocks[-1]['bubbletrap_setting'] and 
        pfcData.get(purge_blocks[-1]['inlet_setting']).get('qd') == purge_blocks[-1]['inlet_QD_setting']
    )

    allInletsPurged = True
    inletsNotPurged = []
    for val in remainingInlets:
        if (pfcData.get(val).get('qd')).strip() != '':
            allInletsPurged = False
            inletsNotPurged.append(val)
    
    all_correct = standard_settings_correct and last_purge_correct and lastPurgeBuffer and allInletsPurged

    return purge_blocks, all_correct, lastPurgeBuffer, allInletsPurged, inletsNotPurged
'''
import fitz  # PyMuPDF

def find_manflow_lines(pdf_path):
    # Open PDF document
    doc = fitz.open(pdf_path)
    
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
                        if "manflow" in text.lower():
                            print(text.lower())
                            # Get specific line coordinates
                            x0 = span["origin"][0]  # Left x coordinate
                            y0 = span["origin"][1]  # Top y coordinate
                            x1 = x0 + span["bbox"][2] - span["bbox"][0]  # Right x coordinate
                            y1 = y0 + span["bbox"][3] - span["bbox"][1]  # Bottom y coordinate
                            
                            print(f"Page {page_num + 1}")
                            print(f"Text: {text.strip()}")
                            print(x0, y0, x1, y1)
                            print("-" * 50)
    
    doc.close()


find_manflow_lines("v001 scouting method LB2273 ProA.pdf")

#check_purge_blocks_settings_from_pdf("v001 scouting method LB2273 ProA.pdf")

