import streamlit as st
import re
from extractText import extract_text_from_pdf
from extractPFCData import output_PFC_params
from extractText import extract_unit_opertaion_from_method
from streamlit_pdf_viewer import pdf_viewer
import base64
import streamlit.components.v1 as components
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextBoxHorizontal
from annotatePDF import annotate_doc
from proAMainLoop import find_highlight_loc
from blockVerification import check_purge_block_settings, check_MS_blocks_settings_pdf, check_column_params, check_indiv_blocks_settings_pdf


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
    
        default_qd_map['Sample']['qd'] = 'QD00015'
        default_qd_map['Inlet4']['flow_rate'] = '300'
        default_qd_map['Inlet1']['flow_rate'] = '300'

    st.header("Verify Column Parameters")
    column_disabled = uploaded_PFC_file is None
    column_params = {'columnHeight': 17, "columnDiameter":45, "contactTime": 15}

    col1, col2, col3 = st.columns(3)
    with col1:
        column_params['columnHeight'] = st.text_input(
            "Column Bed Height",
            value=column_params['columnHeight'],
            key="columnHeight",
            disabled=column_disabled
        )
    with col2:
        column_params['columnDiameter'] = st.text_input(
            "Column Diameter",
            value=column_params['columnDiameter'],
            key="diameter",
            disabled=column_disabled
        )
    with col3:
        column_params['contactTime'] = st.text_input(
            "Contact Time",
            value=column_params['contactTime'],
            key="time",
            disabled=column_disabled
        )
    
    st.header("Verify Number of Mainstreams")
    numMS = st.text_input("Number of Mainstreams",
            value=0,
            key="numMS",
            disabled=column_disabled
        )


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
        'column_params': column_params,
        'uploaded_file': uploaded_file,
        'output_file': outputFile,
        'validation_state': validation_state,
        'submit_pressed': submit_pressed,
        'number_of_MS': numMS
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
            
            # Display results
            st.header("Purge Block Analysis Results")

            # Save uploaded file to disk temporarily
            if result['uploaded_file'] is not None:
                purgeBlockData, inletsNotPurged, equillibrationBlockData, columnParams, individualBlockData = find_highlight_loc(text, result['uploaded_file'], result['inlet_data'])
                highlights = check_purge_block_settings(purgeBlockData, result['inlet_data'])
                highlightsMS = check_MS_blocks_settings_pdf(equillibrationBlockData, result['inlet_data'], result["number_of_MS"])
                highlightsColumnParams = check_column_params(columnParams, result['column_params'])
                highlightsIndiv = check_indiv_blocks_settings_pdf(individualBlockData, result['inlet_data'], result['column_params'])

                mergedHighlights = [item for sublist in [highlights, highlightsMS] for item in sublist]
                mergedHighlights = [item for sublist in [highlightsColumnParams, mergedHighlights] for item in sublist]
                mergedHighlights = [item for sublist in [highlightsIndiv, mergedHighlights] for item in sublist]


                if not highlights:
                    st.success("✅ All purge blocks have correct settings")
                else:
                    st.error("❌ Some purge blocks have incorrect settings")
                
                annotate_doc(result['uploaded_file'], "annotated_example2.pdf", mergedHighlights)

                with st.expander(f"❌ Failed to Purge"):
                    for i in inletsNotPurged:
                        st.write(i + " was not purged with " + result['inlet_data'].get(i).get('qd'))
                display_pdf("annotated_example2.pdf")

     

if __name__ == "__main__":
    main()
