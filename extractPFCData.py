import docx
import re
from pathlib import Path
from extractText import closest_match_unit_op


def read_docx2(file_path):
    """Read content from a docx file separating into nested lists by unit operation"""
    doc = docx.Document(file_path)
    pages = {}
    current_page = []
    first_page = []
    is_first_page = True
    
    def is_unit_op_header(text):
        return "unit" in text.lower() and 'op' in text.lower() and "process flow chart" in text.lower()
    
    def is_downstream_header(text):
        return "Downstream Process Flow Chart" in text
    
    # Process elements in order of appearance
    for element in doc.element.body:
        # Handle paragraphs
        if element.tag.endswith('p'):
            paragraph = element.text.strip()
            if paragraph:
                if is_downstream_header(paragraph):
                    current_page.append(paragraph)
                elif is_unit_op_header(paragraph):
                    # Save previous content
                    if is_first_page:
                        pages["Downstream Process Flow Chart"] = current_page
                        is_first_page = False
                    elif current_page:
                        pages[current_page[0]] = current_page
                    # Start new page with Unit Op header
                    current_page = [paragraph]
                else:
                    current_page.append(paragraph)
        
        # Handle tables
        elif element.tag.endswith('tbl'):
            table = doc.tables[len([e for e in doc.element.body[:doc.element.body.index(element)] 
                                  if e.tag.endswith('tbl')])]
            table_content = []
            for row in table.rows:
                row_text = []
                for cell in row.cells:
                    cell_text = ' '.join(p.text.strip() for p in cell.paragraphs if p.text.strip())
                    if cell_text:
                        row_text.append(cell_text)
                if row_text:
                    table_content.append(' | '.join(row_text))
            current_page.extend(table_content)
    
    # Add final page
    if current_page:
        if is_first_page:
            pages["Downstream Process Flow Chart"] = current_page
        else:
            pages[current_page[0]] = current_page

    return pages


def list_unit_ops(pages):
    unitOperations = []
    for i in pages.keys():
        if "Unit Op" in i:
            unitOperations.append(i)

    return unitOperations
    
def extract_process_info(array):
    process_info = {
        'Regeneration': {'direction': '', 'velocity': '', 'composition': '','residenceTime': 'N/A', 'CV': ' '},
        'Pre Sanitization Rinse': {'direction': '', 'velocity': '--', 'composition': '','residenceTime': 'N/A', 'CV': ' '},
        'Equilibration': {'direction': '', 'velocity': '', 'composition': '','residenceTime': 'N/A', 'CV': ' '},
        'Charge': {'direction': '', 'velocity': '', 'composition': '','residenceTime': 'N/A', 'CV': ' '},
        'Pre Sanitization': {'direction': '', 'velocity': '--', 'composition': '','residenceTime': 'N/A', 'CV': ' '},
        'Post Sanitization': {'direction': '', 'velocity': '--', 'composition': '','residenceTime': 'N/A', 'CV': ' '},
        'Wash 1': {'direction': '', 'velocity': '', 'composition': '','residenceTime': 'N/A', 'CV': ' '},
        'Wash 2': {'direction': '', 'velocity': '', 'composition': '','residenceTime': 'N/A', 'CV': ' '},
        'Wash 3': {'direction': '', 'velocity': '', 'composition': '','residenceTime': 'N/A', 'CV': ' '},
        'Elution': {'direction': '', 'velocity': '', 'composition': '','residenceTime': 'N/A', 'CV': ' '},
        'Storage Rinse': {'direction': '', 'velocity': '', 'composition': '','residenceTime': 'N/A', 'CV': ' '},
        'Post Sanitization Rinse': {'direction': '', 'velocity': '', 'composition': '','residenceTime': 'N/A', 'CV': ' '},
        'Elution': {'direction': '', 'velocity': '', 'composition': '','residenceTime': 'N/A', 'CV': ' '},
        'Storage': {'direction': '', 'velocity': '--', 'composition': '','residenceTime': 'N/A', 'CV': ' '}
    }
    
    default_flow = ''
    current_step = None
    newStep = None
    
    for item in array:
        if 'all column flow directions are downflow' in item.lower():
            default_flow = 'Downflow'
            
        parts = item.split('|')
        parts = [p.strip() for p in parts]
        lower_item = item.lower()

        # Detect current process step
        if 'step' in lower_item:
            if 'regeneration' in lower_item:
                current_step = 'Regeneration'
            elif 'sanitization' in lower_item:
                current_step = 'Post Sanitization'
            elif 'elution' in lower_item:
                current_step = 'Elution'
            elif 'storage' in lower_item:
                current_step = 'Storage'
            elif 'charge' in lower_item:
                current_step = 'Charge'
            
            

        # Handle wash steps specifically
        if 'wash 1' in lower_item:
            current_step = 'Wash 1'
        elif 'wash 2' in lower_item:
            current_step = 'Wash 2'
        elif 'wash 3' in lower_item:
            current_step = 'Wash 3'
        elif 'equilibration' in lower_item:
            current_step = 'Equilibration'
        elif 'pre' in lower_item and ('use' in lower_item or 'sani' in lower_item) and 'rinse' in lower_item:
            current_step = 'Pre Sanitization Rinse'
        elif 'pre' in lower_item and ('use' in lower_item or 'sani' in lower_item) and 'rinse' not in lower_item:
            current_step = 'Pre Sanitization'


        # If we're in a process step, capture its parameters
        if current_step:
            #TODO: if the current step is sanitization or storage, look for a rinse?
            newStep = current_step
            if 'rinse' in lower_item:
                if current_step + " Rinse" in process_info.keys():
                    newStep = current_step + " Rinse"
                

            # Flow direction
            if 'flow direction' in lower_item:
                process_info[newStep]['direction'] = parts[1] if len(parts) > 1 else ''
            # Flow velocity - only capturing NMT value
            elif 'cv' in parts[0].lower() and 'volume' in  parts[0].lower():
                process_info[newStep]['CV'] = parts[1] if len(parts) > 1 else ''
            elif any(term in lower_item for term in ['flow velocity', 'velocity', 'flow:', 'residence']):

                # Extract the NMT value
                try:
                    value = item[item.lower().find('nmt'):].split()[1]
                    process_info[newStep]['velocity'] = value
                except:
                    pass

                try:
                    value = item[item.lower().find('nlt'):].split()[1]
                    process_info[newStep]['residenceTime'] = value

                except:
                    pass
            # Composition
            elif any(term in lower_item for term in ['composition:', 'buffer composition']):
                process_info[newStep]['composition'] = parts[1] if len(parts) > 1 else ''

        

    #sometimes parameters are shared across charge and equilibration, if one is empty and the other has a value, replace the empty value
    for key in process_info['Charge'].keys():
        if key!= 'CV':
            if process_info['Charge'][key].strip() == '' and process_info['Equilibration'][key].strip() != '':
                process_info['Charge'][key] = process_info['Equilibration'][key]
            elif process_info['Charge'][key].strip() != '' and process_info['Equilibration'][key].strip() == '':
                process_info['Equilibration'][key] = process_info['Charge'][key]

    #parameters are assumed to be shared across a rinse and a buffer step if it is not specified in the pfc
    checks = ['direction', 'velocity', 'composition']
    for key in process_info.keys():
        for param in checks:
            if key + " Rinse" in process_info.keys() and process_info[key][param].strip() !='' and process_info[key + ' Rinse'][param].strip() == '':
                process_info[key + ' Rinse'][param] = process_info[key][param].strip()



    # Set default flow direction if not specified
    for step in process_info:
        if process_info[step]['direction'] == '' and default_flow:
            process_info[step]['direction'] = default_flow


    return process_info



def output_PFC_params(PFCInput, unitOperationInMethod):

    textPages = read_docx2(PFCInput)

    unit_operations = list_unit_ops(textPages)

    bestMatchUnitOp, ratio = closest_match_unit_op(unitOperationInMethod, unit_operations)


    for unitOp in unit_operations:
        if bestMatchUnitOp.lower() in unitOp.lower():
            details = textPages.get(unitOp)
            process_info = extract_process_info(details)

            return process_info


