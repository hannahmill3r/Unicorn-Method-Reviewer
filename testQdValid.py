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
from proAMainLoop import find_highlight_loc, calc_LFlow
from blockVerification import check_purge_block_settings, check_watch_settings, check_MS_blocks_settings_pdf, check_column_params, check_indiv_blocks_settings_pdf, check_end_of_run_pdf, check_scouting, calc_LFlow_from_residence_time


def writeColumns(default_qd_map, requiredBuffers, inputs_disabled, directOptions):
    """
    Creates a Streamlit interface for configuring pump parameters for both Pump A and B inlets
    
    Args:
        default_qd_map (dict): Dictionary containing default values for each buffer
        requiredBuffers (list): List of buffers that are required and should be marked with *
        inputs_disabled (bool): Whether input fields should be disabled
        directOptions (list): Available options for flow direction
    """
    
    # Helper function to create input fields for a buffer
    def create_buffer_inputs(buffer, inlet):
        """Creates standardized input fields for each buffer"""
        # Create 5 columns with specific width ratios
        cols = st.columns([2.25, 3,3,3,3,3], vertical_alignment="center")
        
        # Column 0: Buffer name (with * if required)
        with cols[0]:
            buffer_label = f"{buffer}*" if buffer in requiredBuffers else buffer
            st.write(buffer_label)
            
        # Create input fields across columns
        field_configs = [
            ('qd', f"{inlet} QD Number", f"{buffer}_qd", "QD"),
            ('flow_rate', f"{inlet} Flow Rate (cm/h)", f"{buffer}_flow", "Flow Rate"),
            ('direction', f"{inlet} Flow Direction", f"{buffer}_direction", "Flow Direction"),
            ('residence time', f"{inlet} Residence Time (NLT)", f"{buffer}_residence_time", "Residence Time"),
            ('CV', f"{inlet} Column Volume (CV)", f"{buffer}_CV", f"{buffer} Volume (CV)")
        ]
        
        # Create input fields in columns 1-4
        for i, (key, helpLabel, field_key, label) in enumerate(field_configs, 1):
            with cols[i]:
                if key == 'direction':
                    # Special handling for direction dropdown
                    default_qd_map[buffer][key] = st.selectbox(
                        label,
                        directOptions,
                        help = helpLabel,
                        key=field_key,
                        index=directOptions.index(default_qd_map[buffer].get(key)),
                        disabled=inputs_disabled
                    )
                else:
                    # Standard text input for other fields
                    default_qd_map[buffer][key] = st.text_input(
                        label,
                        value=default_qd_map[buffer].get(key),
                        help = helpLabel,
                        key=field_key,
                        disabled=inputs_disabled
                    )

    # Process Pump A Inlets
    pump_a_buffers = ['Equilibration', 'Elution', 'Wash 1', "Wash 3", 'Charge', 'Pre Sanitization', 'Pre Sanitization Rinse', 'Storage Rinse']
    for buffer in pump_a_buffers:
        create_buffer_inputs(buffer, default_qd_map[buffer].get('inlet'))

    # Process Pump B Inlets
    st.subheader("Pump B Inlets")
    pump_b_buffers = ['Post Sanitization', 'Post Sanitization Rinse', 'Storage', 'Regeneration', 'Wash 2']
    for buffer in pump_b_buffers:
        create_buffer_inputs(buffer, default_qd_map[buffer].get('inlet'))

def display_pdf(file):
    # Opening file from file path
    with open(file, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    
    # Embedding PDF in HTML
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    
    # Displaying File
    st.markdown(pdf_display, unsafe_allow_html=True)



def create_inlet_qd_interface():

    #st.set_page_config(layout="wide")
    st.set_page_config(
    page_title="UNICORN Method Validator",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "# This is a header. This is an *extremely* cool app!"
    }
)
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
        'Equilibration': {'inlet': 'Inlet 1', 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' '},
        'Elution': {'inlet': 'Inlet 2', 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' '},
        'Wash 1': {'inlet': 'Inlet 3', 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' '},
        'Wash 3': {'inlet': 'Inlet 3', 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' '},
        'Charge': {'inlet': 'Sample', 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' '},
        'Storage': {'inlet': 'Inlet 5', 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' '},
        'Regeneration': {'inlet': 'Inlet 6', 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' '},
        'Pre Sanitization': {'inlet': 'Inlet 4', 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' '},
        'Pre Sanitization Rinse': {'inlet': 'Inlet 1', 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' '},
        'Post Sanitization': {'inlet': 'Inlet 4', 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' '},
        'Post Sanitization Rinse': {'inlet': 'Inlet 1', 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' '},
        'Storage Rinse': {'inlet': 'Inlet 1', 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' '},
        'Wash 2': {'inlet': 'Inlet 7', 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' '}
    }
    



    st.header("Verify Column Parameters")
    column_disabled = uploaded_PFC_file is None
    column_params = {'columnHeight': '', "columnDiameter":'', "contactTime": ''}

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
    
    st.header("Verify Number of Mainstreams and Cycles")
    col1, col2 = st.columns(2)
    with col1:
        numMS = st.text_input("Number of Mainstreams",
                value=0,
                key="numMS",
                disabled=column_disabled
            )
    with col2:
        numCycles = st.text_input("Number of Cycles",
                value=0,
                key="numCycles",
                disabled=column_disabled
            )
        
    if int(numCycles)!=0 and int(numMS)!=0 and int(numCycles)%int(numMS)!=0:
        st.error("Expected the number of cycles to be divisible by number of mainstreams, please double check this")
        
    
    columnParamsIncomplete = True
    for key in column_params.keys():
        if column_params[key].strip() =='':
            columnParamsIncomplete = True
        else:
            columnParamsIncomplete = False

    inputs_disabled = uploaded_PFC_file is None or columnParamsIncomplete
    def fill_default_sample_map(default_qd_map, column_params):
        
        qdMap = output_PFC_params(uploaded_PFC_file, selected_option)
          

        for i in default_qd_map.keys():
            
            qdAssignment = qdMap.get(i).get('composition')
            directionAssignment = qdMap.get(i).get('direction')
            residenceAssignment =  qdMap.get(i).get('residenceTime')
            cvAssignment =  qdMap.get(i).get('CV')

            if 'sani' in i.lower():
                velocityAssignment = round(calc_LFlow(float(column_params['columnHeight']), float(column_params['columnDiameter']), float(column_params['contactTime']))["linearFlow"])
            elif 'charge' in i.lower() or 'wash 1' in i.lower() and residenceAssignment.isdigit():
                velocityAssignment = round(calc_LFlow_from_residence_time(float(column_params['columnHeight']), float(residenceAssignment)))
            else:
                velocityAssignment =  qdMap.get(i).get('velocity')

            default_qd_map[i]['qd'] = qdAssignment
            default_qd_map[i]['flow_rate'] = velocityAssignment
            default_qd_map[i]['direction'] = directionAssignment
            default_qd_map[i]['residence time'] = residenceAssignment
            default_qd_map[i]['CV'] = cvAssignment
        return default_qd_map
    
    if not inputs_disabled:
        default_qd_map = fill_default_sample_map(default_qd_map, column_params)


    st.header("Verify Inlet Parameters")


    # Create columns for Pump A Inlets
    st.subheader("Pump A Inlets")
    directOptions = ['Downflow', 'Upflow', ' ']
    requiredBuffers = ['Post Sanitization', 'Equilibration', 'Wash 1', 'Storage']
    
    writeColumns(default_qd_map, requiredBuffers, inputs_disabled, directOptions)
    

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
        invalidError = []

        #check if any required feilds are empty
        for buffer in requiredBuffers:
            if not default_qd_map[buffer]['qd'].strip() or not default_qd_map[buffer]['flow_rate'].strip() or not default_qd_map[buffer]['direction'].strip():
                invalidError.append(f"{buffer} is missing required information")
            

        # Check QD format for all fields that have values
        for buffer in default_qd_map.keys():
            qd = default_qd_map[buffer]['qd']
            if qd.strip() and not is_valid_qd(qd):
                invalidError.append(f"Invalid QD format for {buffer}. Format should be 'QD' followed by 5 digits (e.g., QD00015)")
            try:
                flowRateNumber = float(default_qd_map[buffer]['flow_rate'])
            except:
                if default_qd_map[buffer]['flow_rate'].strip():
                    invalidError.append(f"Expected flow rate to be a number for {buffer}. (e.g., 300)")
        
        if invalidError == []:
            st.success("All parameters are valid!")
            st.session_state['qd_validated'] = True
            validation_state['is_valid'] = True
        else:
            st.session_state['qd_validated'] = False
            validation_state['is_valid'] = False
            col1 = st.columns(1)
            st.error('\n\n'.join(invalidError))


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
                purgeBlockData, inletsNotPurged, equillibrationBlockData, columnParams, individualBlockData, watchBlockData, finalBlock, scoutingData = find_highlight_loc(text, result['uploaded_file'], result['inlet_data'])
                highlights = check_purge_block_settings(purgeBlockData, result['inlet_data'])
                highlightsMS = check_MS_blocks_settings_pdf(equillibrationBlockData, result['inlet_data'], result["number_of_MS"])
                highlightsColumnParams = check_column_params(columnParams, result['column_params'])
                highlightsIndiv = check_indiv_blocks_settings_pdf(individualBlockData, result['inlet_data'], result['column_params'])
                highlightsWatchSettings = check_watch_settings(watchBlockData)
                highlightsFinalBlock = check_end_of_run_pdf(finalBlock)
                highlightsScouting = check_scouting(scoutingData, result['inlet_data'])

                mergedHighlights = [item for sublist in [highlights, highlightsScouting, highlightsMS, highlightsColumnParams, highlightsIndiv, highlightsFinalBlock, highlightsWatchSettings] for item in sublist]



                if not mergedHighlights:
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
