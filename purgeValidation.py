import streamlit as st
import re


def find_text_location(pdf_doc, search_text):
        locations = []
        for page_num in range(len(pdf_doc)):
            page = pdf_doc[page_num]
            text_instances = page.search_for(search_text)
            for inst in text_instances:
                locations.append({
                    'page_num': page_num,
                    'coordinates': inst,
                    'text': search_text
                })
        return locations


def get_match_location(match, block_start, full_text):
    if match:
        # Get the start and end positions relative to the block
        start = match.start()
        end = match.end()
        # Adjust positions to be relative to the full text
        absolute_start = block_start + start
        absolute_end = block_start + end
        # Get the line number by counting newlines before this position
        line_number = full_text[:absolute_start].count('\n') + 1
        return {
            'start': absolute_start,
            'end': absolute_end,
            'line': line_number,
            'text': match.group()
        }
    return None


def check_purge_blocks_settings(text, pfcData):
    blocks = text.split("Block: ")
    remainingInlets = list(pfcData.keys())
    purge_blocks = []
    for block in blocks:
        first_line = block.split('\n')[0] if block else ''
        firstBlockAfterPurge = False
        finalPurgeBlock = None
        lastPurgeBuffer = False
        firstPurgeEntered = False
        highlight_locations = {}

        if 'Purge' in first_line:
            firstPurgeEntered = True
            manflow_match = re.search(r'ManFlow:\s*(\d+\.?\d*)\s*{\%}', block)
            column_match = re.search(r'Column:\s*(.*)', block)
            outlet_match = re.search(r'Outlet:\s*(.*)', block)
            bubbletrap_match = re.search(r'BubbleTrap:\s*(.*)', block)
            QD_match = re.search(r'QD\s*(.*)', block)
            base_match = re.search(r'Base:\s*(.*)', block)
            end_block_match = re.search(r'(\d+\.?\d*)\s*End_Block', block)


            inlet_match = re.search(r'Inlet:\s*(.*)', block)

            
            #if any of these values were found, strip them. If no match was found, blank entry
            base_value = base_match.group(1).strip().split(', ')[0] if base_match else ' '
            end_block_value = float(end_block_match.group(1)) if end_block_match else ' '
            flow_value = float(manflow_match.group(1)) if manflow_match else ' '
            column_setting = column_match.group(1).strip() if column_match else ' '
            outlet_setting = outlet_match.group(1).strip() if outlet_match else ' '
            bubbletrap_setting = bubbletrap_match.group(1).strip() if bubbletrap_match else ' '
            QD_match = QD_match.group().strip().replace(" ", "") if QD_match else ' '

            #there is time purge blocks and volume burge blocks, the items we are checking are specific to volume blocks
            if re.search('volume', base_value.lower()): 
                block_name = first_line.strip()
                inlet_number = None
                if inlet_match:
                    inlet_spec = inlet_match.group(1).strip()
                    # Handle cases like "Closed, Inlet4" or "Inlet1, Closed"
                    for part in inlet_spec.split(','):
                        part = part.strip()

                        if 'Inlet' in part and part != 'Inlet':
                            inlet_number = ''.join(filter(str.isdigit, part))
                            inlet_setting = 'Inlet'+inlet_number
                        elif 'Sample' in part:
                            inlet_number = 'Sample'
                            inlet_setting = 'Sample'

                    currentPurgeBlock = ({
                        'block_name': block_name,
                        'manflow': flow_value,
                        'column_setting': column_setting,
                        'outlet_setting': outlet_setting,
                        'bubbletrap_setting': bubbletrap_setting,
                        'inlet_QD_setting': QD_match, 
                        'inlet_setting': inlet_setting,
                        'end_block_setting': end_block_value

                    })


                    purge_blocks.append(currentPurgeBlock)

                    finalPurgeBlock = currentPurgeBlock


                #remove any inlets that are present in purges, list should be empty at end of purges or dict lookups should be blank
                    if inlet_setting in remainingInlets:
                        remainingInlets.pop(remainingInlets.index(inlet_setting))




            
        elif firstPurgeEntered and not firstBlockAfterPurge:
            if finalPurgeBlock is not None:
                
                inlet_match = re.search(r'Inlet:\s*(.*)', block)
                inlet_match = inlet_match.group(1).strip()

                if (finalPurgeBlock['inlet_setting'] in inlet_match):
                    lastPurgeBuffer = True

    
    if not purge_blocks:
        return [], False
        
    standard_settings_correct = all(
        block['manflow'] == 60.0 and 
        ('Bypass_Both' in block['column_setting'] or 'Bypass' in block['column_setting']) and
        block['outlet_setting'] == 'Waste' and
        block['bubbletrap_setting'] == 'Bypass' and pfcData.get(block['inlet_setting']).get('qd') == block['inlet_QD_setting']
        for block in purge_blocks[:-1]
    )
    
    last_purge_correct = (
        purge_blocks[-1]['manflow'] == 60.0 and 
        ('Bypass_Both' in purge_blocks[-1]['column_setting'] or 'Bypass' in purge_blocks[-1]['column_setting']) and
        'Waste' in purge_blocks[-1]['outlet_setting'] and 20.0 == purge_blocks[-1]['end_block_setting'] and
        'Inline' in purge_blocks[-1]['bubbletrap_setting'] and pfcData.get(purge_blocks[-1]['inlet_setting']).get('qd') == purge_blocks[-1]['inlet_QD_setting']
    )

    allInletsPurged = True
    inletsNotPurged = []
    for val in remainingInlets:
        if (pfcData.get(val).get('qd')).strip()!= '':
            allInletsPurged = False
            inletsNotPurged.append(val)

    
    all_correct = standard_settings_correct and last_purge_correct and lastPurgeBuffer and allInletsPurged

    return purge_blocks, all_correct, lastPurgeBuffer, allInletsPurged, inletsNotPurged


def check_purge_blocks_settings_pdf(text, pfcData):
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