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
        return "LB2273 Unit Op" in text and "Process Flow Chart" in text
    
    def is_downstream_header(text):
        return "LB2273 Downstream Process Flow Chart" in text
    
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
        'regeneration': {'direction': '', 'velocity': '', 'composition': ''},
        'equilibration': {'direction': '', 'velocity': '', 'composition': ''},
        'charge': {'direction': '', 'velocity': '', 'composition': ''},
        'sanitization': {'direction': '', 'velocity': '', 'composition': ''},
        'wash1': {'direction': '', 'velocity': '', 'composition': ''},
        'wash2': {'direction': '', 'velocity': '', 'composition': ''},
        'wash3': {'direction': '', 'velocity': '', 'composition': ''},
        'elution': {'direction': '', 'velocity': '', 'composition': ''},
        'storage': {'direction': '', 'velocity': '', 'composition': ''}
    }
    
    default_flow = ''
    current_step = None
    
    for item in array:
        if 'all column flow directions are downflow' in item.lower():
            default_flow = 'Downflow'
            
        parts = item.split('|')
        parts = [p.strip() for p in parts]
        lower_item = item.lower()

        # Detect current process step
        if 'step' in lower_item:
            if 'regeneration' in lower_item:
                current_step = 'regeneration'
            elif 'sanitization' in lower_item:
                current_step = 'sanitization'
            elif 'elution' in lower_item:
                current_step = 'elution'
            elif 'storage' in lower_item:
                current_step = 'storage'
            elif 'charge' in lower_item:
                current_step = 'charge'
            

        # Handle wash steps specifically
        if 'wash 1' in lower_item:
            current_step = 'wash1'
        elif 'wash 2' in lower_item:
            current_step = 'wash2'
        elif 'wash 3' in lower_item:
            current_step = 'wash3'
        elif 'equilibration' in lower_item:
                current_step = 'equilibration'

        # If we're in a process step, capture its parameters
        if current_step:
            # Flow direction
            if 'flow direction' in lower_item:
                process_info[current_step]['direction'] = parts[1] if len(parts) > 1 else ''
            # Flow velocity - only capturing NMT value
            elif any(term in lower_item for term in ['flow velocity', 'velocity', 'flow:']):
                if 'nmt' in lower_item and 'cm/hr' in lower_item:
                    # Extract the NMT value
                    try:
                        value = item[item.lower().find('nmt'):].split()[1]
                        process_info[current_step]['velocity'] = value
                    except:
                        pass
            # Composition
            elif any(term in lower_item for term in ['composition:', 'buffer composition']):
                process_info[current_step]['composition'] = parts[1] if len(parts) > 1 else ''

        # Set default flow direction if not specified
        for step in process_info:
            if process_info[step]['direction'] == '' and default_flow:
                process_info[step]['direction'] = default_flow

    return process_info


def extract_process_info2(array):
    process_info = {
        'regeneration': {'direction': '', 'velocity': '', 'composition': ''},
        'sanitization': {'direction': '', 'velocity': '', 'composition': ''},
        'wash1': {'direction': '', 'velocity': '', 'composition': ''},
        'wash2': {'direction': '', 'velocity': '', 'composition': ''},
        'wash3': {'direction': '', 'velocity': '', 'composition': ''},
        'elution': {'direction': '', 'velocity': '', 'composition': ''},
        'storage': {'direction': '', 'velocity': '', 'composition': ''}
    }
    
    default_flow = ''
    current_step = None
    current_wash = None
    
    for item in array:
        if 'all column flow directions are downflow' in item.lower():
            default_flow = 'Downflow'
            
        parts = item.split('|')
        parts = [p.strip() for p in parts]
        lower_item = item.lower()

        # Detect current process step
        if 'step' in lower_item:
            if 'regeneration' in lower_item:
                current_step = 'regeneration'
            elif 'sanitization' in lower_item:
                current_step = 'sanitization'
            elif 'elution' in lower_item:
                current_step = 'elution'
            elif 'storage' in lower_item:
                current_step = 'storage'

        # Handle wash steps specifically
        if 'wash 1' in lower_item:
            current_step = 'wash1'
        elif 'wash 2' in lower_item:
            current_step = 'wash2'
        elif 'wash 3' in lower_item:
            current_step = 'wash3'

        # If we're in a process step, capture its parameters
        if current_step:
            # Flow direction
            if 'flow direction' in lower_item:
                process_info[current_step]['direction'] = parts[1] if len(parts) > 1 else ''
            # Flow velocity - checking both explicit and implicit cases
            elif any(term in lower_item for term in ['flow velocity', 'velocity', 'flow:']):
                if 'cm/hr' in lower_item and len(parts) > 1:
                    process_info[current_step]['velocity'] = parts[1]
            # Composition
            elif any(term in lower_item for term in ['composition:', 'buffer composition']):
                process_info[current_step]['composition'] = parts[1] if len(parts) > 1 else ''

        # Set default flow direction if not specified
        for step in process_info:
            if process_info[step]['direction'] == '' and default_flow:
                process_info[step]['direction'] = default_flow

    return process_info



def output_PFC_params(PFCInput, unitOperationInMethod):

    textPages = read_docx2(PFCInput)

    unit_operations = list_unit_ops(textPages)

    bestMatchUnitOp = closest_match_unit_op(unitOperationInMethod, unit_operations)


    for unitOp in unit_operations:
        if bestMatchUnitOp.lower() in unitOp.lower():
            details = textPages.get(unitOp)
            process_info = extract_process_info(details)

            return process_info


