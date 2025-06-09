
import re
import numpy as np

def query_block_data(block):
    # Find matches and store their locations
    currentBlock = {}
    filter_match = re.search(r'Filter:\s*(.*)', block)
    outlet_match = re.search(r'Outlet:\s*(.*)', block)
    bubbletrap_match = re.search(r'BubbleTrap:\s*(.*)', block)
    base_match = re.search(r'Base:\s*(.*)', block)
    snapshot_match = re.search(r'Snapshot:\s*(.*)', block)
    inlet_match = re.search(r'Inlet:\s*(.*)', block)

    #TODO this needs to be an interation, in non pro A there may be multiple inlets in two different pumps for the same buffer
    reset_match = re.search(r'FIT\s*(.*)', block)
    fraction_match = re.search(r'Fractions:\s*(.*)', block)
    manflow_match = re.search(r'ManFlow:\s*(\d+\.?\d*)\s*{\%}', block)
    QD_match = re.search(r'QD\s*(.*)', block)
    setmark_match = re.search(r'Set mark:\s*(.*)', block)

    #gradient information
    gradient_mode_match = re.search(r'GradMode::\s*(.*)', block)
    gradient_match = re.search(r'Gradient:\s*(.*)', block)
    gradient_volume_match = re.search(r'(\d+\.?\d*)\s*Gradient:', block)
    gradient_mode_volume_match = re.search(r'(\d+\.?\d*)\s*GradMode:', block)


    #there can be multiple snapshot volumes, we only care about the last one
    snapshot_line =  re.finditer(r'.*Snapshot:', block)
    snapshot_volume_match = ''
    for line in snapshot_line:
        # Extract numbers from the line (will get all numbers including decimals)
        numbers = re.findall(r'\d+\.?\d*', line.group(0))
        snapshot_volume_match = numbers[0] if numbers else ' '

    #there can be multiple comments
    multi_comment_match = re.finditer(r'Comment:\s*(.*)', block)
    commentMatches = []
    for match in multi_comment_match:  
        commentMatches.append(match.group(1).strip() if match else ' ')
    
    
    multi_column_match = re.finditer(r'Column:\s*(.*)', block)
    methodCompFactor = re.search(r'Compensation Factor = \s*(.*)', block)
                            
    columnMatches = []
    for match in multi_column_match:
        columnMatches.append(match.group(1).strip())

    multi_end_block_match = re.finditer(r'(\d+\.?\d*)\s*End_Block', block)
    endMatches = []
    end_block_setting = ''
    for match in multi_end_block_match:  
        endMatches.append(match.group(1).strip() if match else ' ')

    if len(endMatches)>0:
        for val in endMatches[::-1]:
            if float(val)!=float(0.00) or end_block_setting == '':
                end_block_setting = val
                

    #if theres more than one, return string listing all matches. This should only be applicable in the first purge
    if len(columnMatches)>1:
        column_setting = ', '.join(columnMatches)
    elif len(columnMatches) == 1:
        column_setting = ''.join(columnMatches)
    else:
        column_setting = ''


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
    outlet_setting = outlet_match.group(1).strip() if outlet_match else ' '
    bubbletrap_setting = bubbletrap_match.group(1).strip() if bubbletrap_match else ' '
    filter_setting = filter_match.group(1).strip() if filter_match else ' '
    reset_match = reset_match.group(1).strip() if reset_match else ' '
    snapshot_match = snapshot_match.group(1).strip() if snapshot_match else ' '
    setmark_match = setmark_match.group(1).strip() if setmark_match else ' '
    flow_value = float(manflow_match.group(1)) if manflow_match else ' '
    QD_match_value = QD_match.group().strip().replace(" ", "") if QD_match else ' '
    comp_factor = methodCompFactor.group(1).strip() if methodCompFactor else ' '
    grad_mode = gradient_mode_match.group(1).strip() if gradient_mode_match else ' '
    grad_setting = gradient_match.group(1).strip() if gradient_match else ' '
    grad_volume = gradient_volume_match.group(1).strip() if gradient_volume_match else ' '
    grad_mode_volume = gradient_mode_volume_match.group(1).strip() if gradient_mode_volume_match else ' '



    
    inlet_number = None
    if inlet_match:
        inlet_spec = inlet_match.group(1).strip()
        for part in inlet_spec.split(','):
            part = part.strip()
            if 'Inlet' in part and part != 'Inlet':
                inlet_number = ''.join(filter(str.isdigit, part))
                inlet_setting = 'Inlet '+inlet_number
            elif 'Sample' in part:
                inlet_number = 'Sample'
                inlet_setting = 'Sample'

        if inlet_number == None:
            return{}


        if "sample" in inlet_setting.lower():
            inlet_setting = "Inlet 1"

        currentBlock = {
            'column_setting': column_setting,
            'outlet_setting': outlet_setting,
            'bubbletrap_setting': bubbletrap_setting,
            'inlet_setting': inlet_setting,
            'end_block_setting': end_block_setting, 
            'filter_setting': filter_setting, 
            'base_setting': base_value, 
            'reset_setting': reset_match, 
            "flow_setting": ', '.join(flowMatches),
            "flow_tags": flowTags,
            'fraction_setting': numberOfMS, 
            'manflow': flow_value,
            'inlet_QD_setting': QD_match_value, 
            'snapshot_setting': snapshot_match, 
            'setmark_setting': setmark_match, 
            'snapshot_breakpoint_setting': snapshot_volume_match, 
            'compensation_setting': comp_factor, 
            'comments_setting': commentMatches, 
            'grad_mode_setting': grad_mode, 
            'grad_setting': grad_setting, 
            'grad_volume_setting': grad_volume, 
            'grad_mode_volume_setting': grad_mode_volume

        }
    return currentBlock


def query_watch(block):
    # Find matches and store their locations
    watchBlock = {}

    outlet_match = re.search(r'Outlet:\s*(.*)', block)

    snapshot_volume_match = re.finditer(r'(\d+\.?\d*)\s*Snapshot:', block)
    snapVolumeMatches = []
    for match in snapshot_volume_match:  
        snapVolumeMatches.append(match.group(1).strip() if match else ' ')

    multi_snap_match = re.finditer(r'Snapshot:\s*(.*)', block)
    snapMatches = []
    for match in multi_snap_match:  
        snapMatches.append(match.group(1).strip() if match else ' ')

    multi_end_block_match = re.finditer(r'(\d+\.?\d*)\s*End_Block', block)
    endMatches = []
    for match in multi_end_block_match:  
        endMatches.append(match.group(1).strip() if match else ' ')

    #snapshot_volume_match = snapshot_volume_match.group(1).strip() if snapshot_volume_match else ' '



    watch_values = [' '] * 3  # Initialize list with 3 empty spaces
    watch_pattern = re.finditer(r'watch:\s*(.*)', block.lower())
    count = 0
    for watch_match in watch_pattern:
        components = watch_match.group(1).strip().split(', ')
        
        # Find any numeric values associated with 'au'
        for component in components:
            if 'au' in component:
                numbers = [float(token) for token in component.split() 
                          if token.replace('.','').isdigit()]
                if numbers:
                    watch_values[count] = numbers[0]
        count +=1

    outlet_setting = outlet_match.group(1).strip() if outlet_match else ' '

    #if theres more than one, return string listing all matches. This should only be applicable in the first purge

    watchBlock = {
        'frontside_setting': watch_values[0],
        'peak_protect_setting': watch_values[1],
        'backside_setting': watch_values[2], 
        'outlet_setting': outlet_setting, 
        'end_block_setting': endMatches, 
        'snapshot_setting': snapMatches, 
        'snapshot_breakpoint_setting':snapVolumeMatches
    }
    return watchBlock


def query_final_block(block):
    # Find matches and store their locations

    base_match = re.search(r'Base:\s*(.*)', block)
    end_block_match = re.search(r'(\d+\.?\d*)\s*End_Block', block)

    end_block = end_block_match.group(1).strip() if end_block_match else ' '
    base_setting = base_match.group(1).strip() if base_match else ' '


    return{
        'base_setting': base_setting,
        'end_block_setting': end_block
    }

def query_column_data(text):
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
            str1 = re.sub(r'pt', '.', words[ind+1])
            str2 = re.sub(r'pt', '.', words[ind-2])

            str1 = re.findall(r'\d+\.\d+|\d+',  str1)
            if len(str1)>1:
                str1 = '.'.join(str1)
            else:
                str1 = ''.join(str1)

            str2 = re.findall(r'\d+\.\d+|\d+',  str2)
            if len(str2)>1:
                str2 = '.'.join(str2)
            else:
                str2 = ''.join(str2)

            if words[ind-1] =="h":
                columnDiameter = str1
                columnHeight = str2
                
            elif words[ind-1] =="d":
                columnDiameter = str2
                columnHeight = str1

                columnDiameter = re.sub(r'[^0-9.]', '', words[ind-2])
                columnHeight = re.sub(r'[^0-9.]', '', words[ind+1])

    if columnDiameter == 0 or columnHeight == 0:
        return None
    else:
        return {
            "columnDiameter": columnDiameter, 
            "columnHeight": columnHeight, 
            "columnVolume": vc
        }
    
