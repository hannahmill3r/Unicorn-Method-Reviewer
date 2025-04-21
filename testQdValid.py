import streamlit as st
import re
from extractText import extract_text_from_pdf
from extractPFCData import output_PFC_params
from extractText import extract_unit_opertaion_from_method
from purgeValidation import check_purge_blocks_settings_pdf
from streamlit_pdf_viewer import pdf_viewer
import pdfplumber
import base64
import streamlit.components.v1 as components
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import io
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextBoxHorizontal
from annotatePDF import annotate_doc


def display_pdf(file):
    # Opening file from file path
    with open(file, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    
    # Embedding PDF in HTML
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    
    # Displaying File
    st.markdown(pdf_display, unsafe_allow_html=True)



def create_inlet_qd_interface():
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
                qdAssignment = 'QD00015'
                velocityAssignment = '300'
                directionAssignment = ' ' 
                
            else:
                qdAssignment = qdMap.get(ss.get(i)).get('composition')
                velocityAssignment = qdMap.get(ss.get(i)).get('velocity')
                directionAssignment = qdMap.get(ss.get(i)).get('direction')

            default_qd_map[i]['qd'] = qdAssignment
            default_qd_map[i]['flow_rate'] = velocityAssignment
            default_qd_map[i]['direction'] = directionAssignment
    
        default_qd_map['Sample']['qd'] = 'QD00015'
        default_qd_map['Inlet4']['flow_rate'] = '300'
        default_qd_map['Inlet1']['flow_rate'] = '300'

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
        col1, col2, col3 = st.columns(3, vertical_alignment = "center")

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
    result = create_inlet_qd_interface()

    if result['submit_pressed']:
        st.info("Processing document and comparing QD numbers...")
        
        # Process the PDF and analyze purge blocks
        outputFile = extract_text_from_pdf(result['uploaded_file'], 'output2')
        #st.markdown(f'<pre>{text}</pre>', unsafe_allow_html=True)
        

        with open(outputFile, 'r') as file:
            text = file.read()
            
            

            # Check purge blocks
            purge_blocks, all_correct, lastPurgeBuffer, allInletsPurged, inletsNotPurged = check_purge_blocks_settings_pdf(text, result['inlet_data'])
            
            # Display results
            st.header("Purge Block Analysis Results")
            
            if all_correct:
                st.success("✅ All purge blocks have correct settings")
            else:
                st.error("❌ Some purge blocks have incorrect settings")
            
            st.subheader("Detailed Block Settings:")

            all_incorrect = []
            for block in purge_blocks:
                # Validate settings for this block
                is_last_block = block == purge_blocks[-1]

                incorrect_settings = []
                
                # Check each setting and add to list if incorrect
                if block['manflow'] != 60.0:
                    incorrect_settings.append(('ManFlow', block['manflow'], '60.0%', block['locations'].get('manflow')))
                    
                if not ('Bypass_Both' in block['column_setting'] or 'Bypass' in block['column_setting']):
                    incorrect_settings.append(('Column', block['column_setting'], 'Bypass_Both', block['locations'].get('column')))
                    
                if block['outlet_setting'] != 'Waste':
                    incorrect_settings.append(('Outlet', block['outlet_setting'], 'Waste', block['locations'].get('outlet')))
                    
                expected_bubbletrap = 'Inline' if is_last_block else 'Bypass'
                if block['bubbletrap_setting'] != expected_bubbletrap:
                    incorrect_settings.append(('BubbleTrap', block['bubbletrap_setting'], expected_bubbletrap, block['locations'].get('bubbletrap')))

                expected_qdNumber = result['inlet_data'].get(block['inlet_setting']).get('qd')
                if expected_qdNumber.strip() != block['inlet_QD_setting']:
                    incorrect_settings.append(('QD Number', block['inlet_QD_setting'], expected_qdNumber, block['locations'].get('QD')))
                
                if is_last_block:
                    if 20.0 != block['end_block_setting']:
                        incorrect_settings.append(('Final Purge should be 20L', block['end_block_setting'], 20.0, block['locations'].get('endBlock')))
                        
                
                all_incorrect.extend(incorrect_settings)
                # Only show blocks with incorrect settings
                if incorrect_settings:
                    with st.expander(f"❌ Block: {block['block_name']}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write("Incorrect Settings:")
                            for setting, current_value, expected_value, location in incorrect_settings:
                                st.write(f"• {setting}: {current_value}")
                        with col2:
                            st.write("Expected Values:")
                            for setting, current_value, expected_value, location in incorrect_settings:
                                st.write(f"• {setting}: {expected_value}")

                    

            


            with st.expander(f"❌ Failed to Purge"):
                for i in inletsNotPurged:
                    st.write(i + " was not purged with " + result['inlet_data'].get(i).get('qd'))
            

            highlights = [
                {
                    'page': 0,
                    'loc': (104.03028869628906, 97.61709594726562, 131.03839111328125, 108.64652252197266),
                    'text': "This is an important section"
                }, 
                {
                    'page': 0,
                    'loc': (130, 382, 267, 400),
                    'text': "This is an important section"
                }, 
                {
                    'page': 0,
                    'loc': (71.63995361328125, 471.6002502441406, 574.667724609375, 482.62966918945314),
                    'text': "This is an important section"
                }

            ]


            # Save uploaded file to disk temporarily
            if result['uploaded_file'] is not None:
                annotate_doc(result['uploaded_file'], "annotated_example2.pdf", highlights)
                display_pdf("annotated_example2.pdf")

     

if __name__ == "__main__":
    main()
