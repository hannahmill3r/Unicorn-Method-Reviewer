import streamlit as st
import re
from extractText import extract_text_from_pdf
from extractPFCData import output_PFC_params
from extractText import extract_unit_opertaion_from_method

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

            
            if base_match:
                base_value = base_match.group(1).strip().split(', ')[0]
            else:
                base_value = ' '
            
            if end_block_match:
                end_block_value = float(end_block_match.group(1))

            else:
                end_block_match = ' '

            if manflow_match:
                flow_value = float(manflow_match.group(1))
            else:
                flow_value = ' '
            if column_match:
                column_setting = column_match.group(1).strip()
            else:
                column_setting = ' '
            if outlet_match:
                outlet_setting = outlet_match.group(1).strip()
            else:
                outlet_setting = ' '
            if bubbletrap_match:
                bubbletrap_setting = bubbletrap_match.group(1).strip()
            else:
                bubbletrap_setting = ' '
            if QD_match:
                QD_match = QD_match.group().strip().replace(" ", "")
            else:
                QD_match = ' '

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


def create_inlet_qd_interface2():
    st.title("UNICORN Method Validator")

    uploaded_file = st.file_uploader("Upload UNICORN Method PDF", type="pdf")
    uploaded_PFC_file = None
    outputFile = None

    options = ['None', 'Detergent Viral Inactivation', 'Protein A Capture Chromatography', 
               'Low pH Viral Inactivation and Clarification', 'Cation Exchange Chromatography', 
               'Viral Filtration', 'Tangential Flow Filtration', 
               'Intermediate Drug Substance Dispensing and Storage']
   
    if uploaded_file is not None:
        options = ['Detergent Viral Inactivation', 'Protein A Capture Chromatography',
                  'Low pH Viral Inactivation and Clarification', 'Cation Exchange Chromatography',
                  'Viral Filtration', 'Tangential Flow Filtration',
                  'Intermediate Drug Substance Dispensing and Storage']
        outputFile = extract_text_from_pdf(uploaded_file, 'output2')
        unitOperationFromMethod = extract_unit_opertaion_from_method(outputFile, options)
        selected_option = st.selectbox('Verify Unit Operation:', options, 
                                     index=options.index(unitOperationFromMethod), disabled=False)

        if selected_option is not None:
            uploaded_PFC_file = st.file_uploader("Upload PFC Word Document Containing " + 
                                               unitOperationFromMethod + " Information", type="docx")
    else:
        options = ['None']
        selected_option = st.selectbox('Verify Unit Operation:', options, 
                                     index=options.index('None'), disabled=True)
        st.info("Please upload UNICORN Method PDF first before uploading PFC document")

    default_qd_map = {
        'Inlet1': {'qd': ' ', 'flow_rate': ' ', 'direction': ' '},
        'Inlet2': {'qd': ' ', 'flow_rate': ' ', 'direction': ' '},
        'Inlet3': {'qd': ' ', 'flow_rate': ' ', 'direction': ' '},
        'Sample': {'qd': ' ', 'flow_rate': ' ', 'direction': ' '},
        'Inlet4': {'qd': ' ', 'flow_rate': ' ', 'direction': ' '},
        'Inlet5': {'qd': ' ', 'flow_rate': ' ', 'direction': ' '},
        'Inlet6': {'qd': ' ', 'flow_rate': ' ', 'direction': ' '},
        'Inlet7': {'qd': ' ', 'flow_rate': ' ', 'direction': ' '}
    }
    
    inputs_disabled = uploaded_PFC_file is None

    if not inputs_disabled:
        qdMap = output_PFC_params(uploaded_PFC_file, selected_option)
        ss = {'Inlet1': 'equilibration', 'Inlet2': 'elution', 'Inlet3': 'wash3', 
              'Sample': 'charge','Inlet4': 'sanitization', 'Inlet5': 'storage', 
              'Inlet6': 'regeneration', 'Inlet7': 'wash2'}  

        for i in default_qd_map.keys():
            if qdMap.get(ss.get(i)) == None:
                qdAssignment = ' '
                velocityAssignment = ' ' 
                directionAssignment = ' ' 
            else:
                qdAssignment = qdMap.get(ss.get(i)).get('composition')
                velocityAssignment = qdMap.get(ss.get(i)).get('velocity')
                directionAssignment = qdMap.get(ss.get(i)).get('direction')

            default_qd_map[i]['qd'] = qdAssignment
            default_qd_map[i]['flow_rate'] = velocityAssignment
            default_qd_map[i]['direction'] = directionAssignment

    st.header("Verify Inlet Parameters")
    
    # Create columns for Pump A Inlets
    st.subheader("Pump A Inlets")
    inlet_data = {}
    directOptions = ['Downflow', 'Upflow', ' ']
    
    for inlet in ['Inlet1', 'Inlet2', 'Inlet3', 'Sample']:
        col1, col2, col3 = st.columns(3)
        with col1:
            inlet_data[f'{inlet}_qd'] = st.text_input(
                f"{inlet} QD Number",
                value=default_qd_map[inlet]['qd'],
                key=f"{inlet}_qd",
                disabled=inputs_disabled
            )
        with col2:
            inlet_data[f'{inlet}_flow'] = st.text_input(
                f"{inlet} Flow Rate (cm/h)",
                value=default_qd_map[inlet]['flow_rate'],
                key=f"{inlet}_flow",
                disabled=inputs_disabled
            )
        with col3:
            inlet_data[f'{inlet}_direction'] = st.selectbox(
                f"{inlet} Flow Direction",
                directOptions,
                key=f"{inlet}_direction",
                index=directOptions.index(default_qd_map[inlet]['direction']),
                disabled=inputs_disabled
            )

    # Create columns for Pump B Inlets
    st.subheader("Pump B Inlets")
    for inlet in ['Inlet4', 'Inlet5', 'Inlet6', 'Inlet7']:
        col1, col2, col3 = st.columns(3)
        with col1:
            inlet_data[f'{inlet}_qd'] = st.text_input(
                f"{inlet} QD Number",
                value=default_qd_map[inlet]['qd'],
                key=f"{inlet}_qd",
                disabled=inputs_disabled
            )
        with col2:
            inlet_data[f'{inlet}_flow'] = st.text_input(
                f"{inlet} Flow Rate (cm/h)",
                value=default_qd_map[inlet]['flow_rate'],
                key=f"{inlet}_flow",
                disabled=inputs_disabled
            )
        with col3:
            inlet_data[f'{inlet}_direction'] = st.selectbox(
                f"{inlet} Flow Direction",
                directOptions,
                key=f"{inlet}_direction",
                index=directOptions.index(default_qd_map[inlet]['direction']),
                disabled=inputs_disabled
            )

    def is_valid_qd(qd):
        qd = qd.strip(' ')
        if not qd:  # Allow empty entries
            return True
        elif qd[0:2].upper() == "QD" and qd[2:].isdigit():
            return True
        else:
            return False

    validation_state = {'is_valid': False}

    validate_button = st.button("Validate Parameters", disabled=inputs_disabled)
    
    if validate_button:
        all_valid = True
        for inlet in default_qd_map.keys():
            qd = inlet_data[f'{inlet}_qd']
            if qd and not is_valid_qd(qd):
                st.error(f"Invalid QD format for {inlet}. Format should be 'QD' followed by 5 digits (e.g., QD00015)")
                all_valid = False
        
        if all_valid:
            st.success("All parameters are valid!")
            st.session_state['qd_validated'] = True
            validation_state['is_valid'] = True
        else:
            st.session_state['qd_validated'] = False
            validation_state['is_valid'] = False

    submit_pressed = st.button(
        "Submit for Comparison", 
        disabled=not (st.session_state.get('qd_validated', False) and uploaded_file is not None)
    )

    return {
        'inlet_data': default_qd_map,
        'uploaded_file': uploaded_file,
        'output_file': outputFile,
        'validation_state': validation_state,
        'submit_pressed': submit_pressed
    }


def main():
    result = create_inlet_qd_interface2()

    if result['submit_pressed']:
        st.info("Processing document and comparing QD numbers...")
        
        # Process the PDF and analyze purge blocks
        outputFile = extract_text_from_pdf(result['uploaded_file'], 'output2')
        with open(outputFile, 'r') as file:
            text = file.read()
            

            # Check purge blocks
            purge_blocks, all_correct, lastPurgeBuffer, allInletsPurged, inletsNotPurged = check_purge_blocks_settings(text, result['inlet_data'])
            
            # Display results
            st.header("Purge Block Analysis Results")
            
            if all_correct:
                st.success("✅ All purge blocks have correct settings")
            else:
                st.error("❌ Some purge blocks have incorrect settings")
            
            st.subheader("Detailed Block Settings:")

            for block in purge_blocks:
                # Validate settings for this block
                is_last_block = block == purge_blocks[-1]

                incorrect_settings = []
                
                # Check each setting and add to list if incorrect
                if block['manflow'] != 60.0:
                    incorrect_settings.append(('ManFlow', block['manflow'], '60.0%'))
                    
                if not ('Bypass_Both' in block['column_setting'] or 'Bypass' in block['column_setting']):
                    incorrect_settings.append(('Column', block['column_setting'], 'Bypass_Both'))
                    
                if block['outlet_setting'] != 'Waste':
                    incorrect_settings.append(('Outlet', block['outlet_setting'], 'Waste'))
                    
                expected_bubbletrap = 'Inline' if is_last_block else 'Bypass'
                if block['bubbletrap_setting'] != expected_bubbletrap:
                    incorrect_settings.append(('BubbleTrap', block['bubbletrap_setting'], expected_bubbletrap))

                expected_qdNumber = result['inlet_data'].get(block['inlet_setting']).get('qd')
                if expected_qdNumber.strip() != block['inlet_QD_setting']:
                    incorrect_settings.append(('QD Number', block['inlet_QD_setting'], expected_qdNumber))
                
                if is_last_block:
                    if 20.0 != block['end_block_setting']:
                        incorrect_settings.append(('Final Purge should be 20L', block['end_block_setting'], 20.0))
                
                # Only show blocks with incorrect settings
                if incorrect_settings:
                    with st.expander(f"❌ Block: {block['block_name']}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write("Incorrect Settings:")
                            for setting, current_value, expected_value in incorrect_settings:
                                st.write(f"• {setting}: {current_value}")
                        with col2:
                            st.write("Expected Values:")
                            for setting, current_value, expected_value in incorrect_settings:
                                st.write(f"• {setting}: {expected_value}")

            with st.expander(f"❌ Failed to Purge"):
                for i in inletsNotPurged:
                    st.write(i + " was not purged with" + result['inlet_data'].get(i).get('qd'))

if __name__ == "__main__":
    main()
