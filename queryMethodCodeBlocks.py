
import re
import numpy as np



def queryIndividualBlocks(block):
    # Find matches and store their locations
    currentBlock = {}
    column_match = re.search(r'Column:\s*(.*)', block)
    filter_match = re.search(r'Filter:\s*(.*)', block)
    outlet_match = re.search(r'Outlet:\s*(.*)', block)
    bubbletrap_match = re.search(r'BubbleTrap:\s*(.*)', block)
    base_match = re.search(r'Base:\s*(.*)', block)
    end_block_match = re.search(r'(\d+\.?\d*)\s*End_Block', block)
    inlet_match = re.search(r'Inlet:\s*(.*)', block)
    reset_match = re.search(r'FIT\s*(.*)', block)
    fraction_match = re.search(r'Fractions:\s*(.*)', block)
    manflow_match = re.search(r'ManFlow:\s*(\d+\.?\d*)\s*{\%}', block)
    QD_match = re.search(r'QD\s*(.*)', block)
    snapshot_match = re.search(r'Snapshot:\s*(.*)', block)
    setmark_match = re.search(r'Set mark:\s*(.*)', block)


    numberOfMS = 0
    if fraction_match:
        fraction_spec = fraction_match.group(1).strip()
        numberOfMS = fraction_spec.split(',')[0]
    else:
        numberOfMS = ' '

    
    multi_flow_match = re.finditer(r' Flow:\s*(.*)', block)
    flowMatches = []
    flowTags = []
    for match in multi_flow_match:
        flowTag = re.search(r'#\s*(.*)', match.group(1).strip()).group(1).strip()
        flowMatches.append(''.join(filter(str.isdigit, match.group(1).strip().split('#')[0])))
        flowTags.append(flowTag)


    base_value = base_match.group(1).strip().split(', ')[0] if base_match else ' '
    end_block_value = float(end_block_match.group(1)) if end_block_match else ' '
    column_setting = column_match.group(1).strip() if column_match else ' '
    outlet_setting = outlet_match.group(1).strip() if outlet_match else ' '
    bubbletrap_setting = bubbletrap_match.group(1).strip() if bubbletrap_match else ' '
    filter_setting = filter_match.group(1).strip() if filter_match else ' '
    reset_match = reset_match.group(1).strip() if reset_match else ' '
    snapshot_match = snapshot_match.group(1).strip() if snapshot_match else ' '
    setmark_match = setmark_match.group(1).strip() if setmark_match else ' '
    flow_value = float(manflow_match.group(1)) if manflow_match else ' '
    QD_match_value = QD_match.group().strip().replace(" ", "") if QD_match else ' '


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

        if inlet_number == None:
            return{}


        currentBlock = {
            'column_setting': column_setting,
            'outlet_setting': outlet_setting,
            'bubbletrap_setting': bubbletrap_setting,
            'inlet_setting': inlet_setting,
            'end_block_setting': end_block_value, 
            'filter_setting': filter_setting, 
            'base_setting': base_value, 
            'reset_setting': reset_match, 
            "flow_setting": ', '.join(flowMatches),
            "flow_tags": flowTags,
            'fraction_setting': numberOfMS, 
            'manflow': flow_value,
            'inlet_QD_setting': QD_match_value, 
            'snapshot_setting': snapshot_match, 
            'setmark_setting': setmark_match
        }

    return currentBlock


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
