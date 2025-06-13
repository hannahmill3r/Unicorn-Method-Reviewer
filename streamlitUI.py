import streamlit as st
from extractText import extract_text_from_pdf
from extractPFCData import output_PFC_params
from extractText import extract_unit_opertaion_from_method
import base64
import tempfile
import fitz
import re
from flowCalculations import calc_LFlow, calc_LFlow_from_residence_time
from bugReporting import create_bug_report_menu
from blockNameDict_user_validation import *

def parse_gradient_composition(text):
    # Regular expression to match patterns like "90% A: QD0030510% B: QD00346"
    pattern = r'(\d+)%\s*A:\s*(QD\d+)\s*(\d+)%\s*B:\s*(QD\d+)'
    
    match = re.search(pattern, text)
    if match:
        buffer_a_percent = match.group(1)
        buffer_a_qd = match.group(2)
        buffer_b_percent = match.group(3)
        buffer_b_qd = match.group(4)
        
        return {
            'Buffer A': {'percent': buffer_a_percent, 'QD': buffer_a_qd},
            'Buffer B': {'percent': buffer_b_percent, 'QD': buffer_b_qd}
        }
    return None

def define_field_config(buffer,inlet):
    """
    This function is used to create pre-defined field configuration 
    :param buffer: buffer name to associate the configuration
    :param inlet: inlet for the buffer
    :return :list of tuples
    """
    # Create input fields across columns
    field_configs = [
        ('qd', f"{inlet} QD Number", f"{buffer}_qd", "QD"),
        ('flow_rate', f"{inlet} Flow Rate (cm/h)", f"{buffer}_flow", "Flow Rate"),
        ('direction', f"{inlet} Flow Direction", f"{buffer}_direction", "Flow Direction"),
        ('residence time', f"{inlet} Residence Time (NLT)", f"{buffer}_residence_time", "Residence Time"),
        ('CV', f"{inlet} Column Volume (CV)", f"{buffer}_CV", f"{buffer} CV")
    ]

    return field_configs

# Helper function to create input fields for a buffer
def create_buffer_inputs(buffer, inlet,default_qd_map,requiredBuffers, inputs_disabled, directOptions, parameters_in_pfc):
    """Creates standardized input fields for each buffer"""
    # Create 5 columns with specific width ratios
    cols = st.columns([2.25, 3,3,3,3,3,1], vertical_alignment="center")

    #input files accross columns
    field_configs = define_field_config(buffer, ', '.join(inlet))

    # Column 0: Buffer name (with * if required)
    with cols[0]:
        buffer_label = f"{buffer}*" if buffer in requiredBuffers else buffer
        st.write(buffer_label)
    
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
                    index=directOptions.index(default_qd_map[buffer].get(key).strip()),
                    disabled=inputs_disabled
                )
            elif key == 'qd' and parse_gradient_composition(default_qd_map[buffer].get(key)):
                parsed_gradient = parse_gradient_composition(default_qd_map[buffer].get(key))

                col5, col6 = st.columns(2)
                default_qd_map[buffer][key] = {
                                            "Buffer A QD": parsed_gradient['Buffer A']['QD'], 
                                            "Buffer A Percent": parsed_gradient['Buffer A']['percent'],
                                            "Buffer B QD": parsed_gradient['Buffer B']['QD'],
                                            "Buffer B Percent": parsed_gradient['Buffer B']['percent'],
                                                }
                
                with col5:
                    default_qd_map[buffer][key]["Buffer A QD"] = st.text_input(
                        label,
                        value=parsed_gradient['Buffer A']['QD'],
                        help = f"Buffer A: {parsed_gradient['Buffer A']['percent']}% {parsed_gradient['Buffer A']['QD']}",
                        key=field_key + "Buffer A",
                        disabled=inputs_disabled
                    )

                    
                with col6:
                    default_qd_map[buffer][key]["Buffer B QD"] = st.text_input(
                        label,
                        value=parsed_gradient['Buffer B']['QD'],
                        help = f"Buffer B: {parsed_gradient['Buffer B']['percent']}% {parsed_gradient['Buffer B']['QD']}",
                        key=field_key + "Buffer B",
                        disabled=inputs_disabled
                    )
                    
            elif key == 'CV' and default_qd_map[buffer].get('isocratic hold').strip() !='':
                col5, col6 = st.columns(2)
                with col5:
                    default_qd_map[buffer][key] = st.text_input(
                        label,
                        value=default_qd_map[buffer].get(key),
                        help = helpLabel,
                        key=field_key,
                        disabled=inputs_disabled
                    )

                
                with col6:
                    default_qd_map[buffer]['isocratic hold'] = st.text_input(
                        'Hold CV',
                        value=default_qd_map[buffer].get('isocratic hold'),
                        help = f"{buffer} Isocratic Hold (CV)",
                        key=field_key + 'isocraticHold',
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
    with cols[6]:
        colx, colempty= st.columns([.01, .99])
        with colx:
            if st.button("X", key=f'{buffer}_delete_key', help="Delete this row", use_container_width = True, type = 'tertiary' ):
                st.session_state.buffers.remove(buffer)
                
                st.rerun()

    

def add_new_buffer(default_qd_map, buffer,inputs_disabled, directOptions):

    """Creates standardized input fields for each buffer
    :param default_qd_map: master qd map dictionary
    :param buffer: buffer name to associate the configuration
    :param inputs_disabled: flag
    :parma directOptions:
    :return :None
    """
   

    # Create 5 columns with specific width ratios
    cols = st.columns([2.25, 3,3,3,3,3,1], vertical_alignment="center")
    inlet = default_qd_map[buffer]['inlet']

    #input files accross columns
    field_configs = define_field_config(buffer,inlet)

    # Column 0: Buffer name (with * if required)
    with cols[0]:
        st.write(buffer)
    
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
                    index=directOptions.index(default_qd_map[buffer].get(key).strip()),
                    disabled=inputs_disabled
                )
            elif key == 'qd' and parse_gradient_composition(default_qd_map[buffer].get(key)):
                parsed_gradient = parse_gradient_composition(default_qd_map[buffer].get(key))

                col5, col6 = st.columns(2)
                default_qd_map[buffer][key] = {
                                            "Buffer A QD": parsed_gradient['Buffer A']['QD'], 
                                            "Buffer A Percent": parsed_gradient['Buffer A']['percent'],
                                            "Buffer B QD": parsed_gradient['Buffer B']['QD'],
                                            "Buffer B Percent": parsed_gradient['Buffer B']['percent'],
                                                }
                
                with col5:
                    default_qd_map[buffer][key]["Buffer A QD"] = st.text_input(
                        label,
                        value=parsed_gradient['Buffer A']['QD'],
                        help = f"Buffer A: {parsed_gradient['Buffer A']['percent']}% {parsed_gradient['Buffer A']['QD']}",
                        key=field_key + "Buffer A",
                        disabled=inputs_disabled
                    )

                    
                with col6:
                    default_qd_map[buffer][key]["Buffer B QD"] = st.text_input(
                        label,
                        value=parsed_gradient['Buffer B']['QD'],
                        help = f"Buffer B: {parsed_gradient['Buffer B']['percent']}% {parsed_gradient['Buffer B']['QD']}",
                        key=field_key + "Buffer B",
                        disabled=inputs_disabled
                    )

            elif key == 'CV' and default_qd_map[buffer].get('isocratic hold').strip() !='':
                col5, col6 = st.columns(2)
                with col5:
                    default_qd_map[buffer][key] = st.text_input(
                        label,
                        value=default_qd_map[buffer].get(key),
                        help = helpLabel,
                        key=field_key,
                        disabled=inputs_disabled
                    )

                
                with col6:
                    default_qd_map[buffer]['isocratic hold'] = st.text_input(
                        'Hold CV',
                        value=default_qd_map[buffer].get('isocratic hold'),
                        help = f"{buffer} Isocratic Hold (CV)",
                        key=field_key + 'isocraticHold',
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

def enable_add_buffer(availableBuffers, default_qd_map,button_key,label,inputs_disabled,directOptions):
    """This function is used to enable additional rows for the Pump sections
    :param availableBuffers: list of buffer for the section
    :param default_qd_map: 
    :param button_key: button key name
    :param label:
    :param inputs_disabled: flag
    :parma directOptions:
    :return :None
    """

    #unique session state key per button
    show_key = f'show_multiselect_{button_key}'
    select_key = f'additional_buffer_{button_key}'

    # Initialize session state
    if show_key not in st.session_state:
        st.session_state[show_key] = False

    #add_buffer_bt = st.button('Add Buffer',key = button_key )

    if st.button(label,key = f'add_buffer_btn_{button_key}'):
        st.session_state[show_key] = True

    if st.session_state[show_key]:
        additional_buffer = [i for i in availableBuffers if i not in st.session_state.buffers]
        new_buffer = st.multiselect('Select Buffer',options = additional_buffer,key = f'additional_buffer_{button_key}')

        for buffer in new_buffer:
            #add_new_buffer(default_qd_map,buffer)
            add_new_buffer(default_qd_map, buffer,inputs_disabled, directOptions)
    

def writeColumns(default_qd_map, requiredBuffers, inputs_disabled, directOptions, parameters_in_pfc):
    """
    Creates a Streamlit interface for configuring pump parameters for both Pump A and B inlets
    
    Args:
        default_qd_map (dict): Dictionary containing default values for each buffer
        requiredBuffers (list): List of buffers that are required and should be marked with *
        inputs_disabled (bool): Whether input fields should be disabled
        directOptions (list): Available options for flow direction
        parameters_in_pfc:
    """
    if 'pfcData' in st.session_state:
        if 'buffers' not in st.session_state:
            st.session_state.buffers = st.session_state.pfcData.copy()


        # Process Pump A Inlets
        st.subheader("Pump A Inlets")
        pump_a_buffers = [key for key, value in default_qd_map.items() if 'A' in value['pump']]

        for buffer in pump_a_buffers:
            if buffer in st.session_state.buffers:
                #create_buffer_inputs(buffer, default_qd_map[buffer].get('inlet'))
                create_buffer_inputs(buffer, default_qd_map[buffer].get('inlet'),default_qd_map,requiredBuffers, inputs_disabled, directOptions, parameters_in_pfc)
                

        # =================================== additional buffer ===================================
        
        enable_add_buffer(pump_a_buffers, default_qd_map,'pump_a','Add Buffer to Pump A ➕',inputs_disabled,directOptions)

        # ==========================================================================================

        # Process Pump B Inlets
        st.subheader("Pump B Inlets")
        pump_b_buffers = [key for key, value in default_qd_map.items() if value['pump'] == 'B']

        for buffer in pump_b_buffers:
            if buffer in st.session_state.buffers:
                #create_buffer_inputs(buffer,pump_b_buffers, default_qd_map[buffer].get('inlet'))
                create_buffer_inputs(buffer, default_qd_map[buffer].get('inlet'),default_qd_map,requiredBuffers, inputs_disabled, directOptions, parameters_in_pfc)

        # =================================== additional buffer ===================================
        
        enable_add_buffer(pump_b_buffers, default_qd_map,'pump_b','Add Buffer to Pump B ➕',inputs_disabled,directOptions)

        # ==========================================================================================

def display_pdf(file):
    # Opening file from file path
    with open(file, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    
    # Embedding PDF in HTML
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    
    # Displaying File
    st.markdown(pdf_display, unsafe_allow_html=True)



def create_inlet_qd_interface():
    parameters_in_pfc = []

    #st.set_page_config(layout="wide")
    st.set_page_config(
    page_title="UNICORN Method Validator",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'About': "The Unicorn Method reviewer takes a dPFC document and parses a specified unit operation. The output is compared against the values described in the provided scouting method's document, highlighting possible transcription errors.",
        'Get help': "mailto:Hannah.miller@lilly.com"
        }
    )
    show_block_name()
    create_bug_report_menu()
    st.title("UNICORN Method Validator")

    uploaded_file = st.file_uploader("Upload UNICORN Method PDF", type="pdf")
    uploaded_PFC_file = None
    outputFile = None

    options = ['None', 'Hydrophobic Interaction Chromatography', 'Protein A Capture Chromatography', 'Cation Exchange Chromatography', 
               'Viral Filtration', 'Tangential Flow Filtration']
    
    
    if uploaded_file is not None:
        
        file_bytes = uploaded_file.read()

        # Save to temp file first
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        try:
            # Open with fitz
            doc = fitz.open(tmp_path)

            # Clone pages into a new document for safe saving
            new_doc = fitz.open()
            for page in doc:
                new_doc.insert_pdf(doc, from_page=page.number, to_page=page.number)

            # Save the cloned document
            new_doc.save("tempfile.pdf", garbage=4, deflate=True)

        except Exception as e:
            st.error(f"Error processing or saving PDF: {e}")

        options = ['Hydrophobic Interaction Chromatography', 'Protein A Capture Chromatography', 'Cation Exchange Chromatography', 
               'Viral Filtration', 'Tangential Flow Filtration']
        
        outputFile = extract_text_from_pdf('tempfile.pdf', 'output2')
        unitOperationFromMethod = extract_unit_opertaion_from_method(outputFile, options)

        selected_unitOperation = st.selectbox('Verify Unit Operation:', options, index=options.index(unitOperationFromMethod), disabled=False)

        if selected_unitOperation is not None:
            uploaded_PFC_file = st.file_uploader("Upload PFC Word Document Containing " + unitOperationFromMethod + " Information", type="docx")
    else:
        options = ['None']
        selected_unitOperation = st.selectbox('Verify Unit Operation:', options, index=options.index('None'), disabled=True)
        st.info("Please upload UNICORN Method PDF first before uploading PFC document")

    PFC_not_uploaded = uploaded_PFC_file is None
    saniStrategyOptions = ["PrismA", "SuRe", "None"]
    if not PFC_not_uploaded:
        try:
            pfcQDMap, saniStrategy, parameters_in_pfc = output_PFC_params(uploaded_PFC_file, selected_unitOperation)
            
            st.session_state['pfcData']= parameters_in_pfc

            selectedSaniStrategy = st.selectbox('Verify Sanitatization Strategy:', saniStrategyOptions, index=saniStrategyOptions.index(saniStrategy), disabled=False)
            
            if not parameters_in_pfc:
                st.write(f"❌ Could not find specified unit operation, please make sure this is a word document dPFC.")

        except Exception as e:
            st.write(f"❌ Could not find specified unit operation, please make sure this is a word document dPFC.")
            PFC_not_uploaded = True
            saniNoOptions = ['None']
            selectedSaniStrategy = st.selectbox('Verify Sanitatization Strategy:', saniNoOptions, index=saniNoOptions.index('None'), disabled=True)
            st.info("Please upload PFC before specifying sanitization strategy")
            print(e)
            

            
    else:
        saniNoOptions = ['None']
        selectedSaniStrategy = st.selectbox('Verify Sanitatization Strategy:', saniNoOptions, index=saniNoOptions.index('None'), disabled=True)
        st.info("Please upload PFC before specifying sanitization strategy")

    if  selected_unitOperation == 'Protein A Capture Chromatography':
        default_qd_map = {
            'Equilibration': {'inlet': ['Inlet 1', 'Closed'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'A', 'isocratic hold': ' '},
            'Elution': {'inlet': ['Inlet 2', 'Closed'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'A', 'isocratic hold': ' '},
            'Wash 1': {'inlet': ['Inlet 3', 'Closed'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'A', 'isocratic hold': ' '},
            'Wash 3': {'inlet': ['Inlet 3', 'Closed'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'A', 'isocratic hold': ' '},
            'Charge': {'inlet': ['Sample', 'Closed'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'A', 'isocratic hold': ' '},
            'Storage': {'inlet': ['Closed', 'Inlet 5'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'B', 'isocratic hold': ' '},
            'Regeneration': {'inlet': ['Closed', 'Inlet 6'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'B', 'isocratic hold': ' '},
            'Pre Sanitization': {'inlet': ['Closed', 'Inlet 4'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'B', 'isocratic hold': ' '},
            'Pre Sanitization Rinse': {'inlet': ['Inlet 1', 'Closed'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'A', 'isocratic hold': ' '},
            'Post Sanitization': {'inlet': ['Closed', 'Inlet 4'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'B', 'isocratic hold': ' '},
            'Post Sanitization Rinse': {'inlet': ['Inlet 1', 'Closed'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'A', 'isocratic hold': ' '},
            'Pre Sanitization 2': {'inlet': ['Closed', 'Inlet 6'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'B', 'isocratic hold': ' '},
            'Pre Sanitization Rinse 2': {'inlet': ['Inlet 1', 'Closed'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'A', 'isocratic hold': ' '},
            'Post Sanitization 2': {'inlet': ['Closed', 'Inlet 6'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'B', 'isocratic hold': ' '},
            'Post Sanitization Rinse 2': {'inlet': ['Inlet 1', 'Closed'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'A', 'isocratic hold': ' '},
            'Storage Rinse': {'inlet': ['Inlet 1', 'Closed'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'A', 'isocratic hold': ' '},
            'Wash 2': {'inlet': ['Closed', 'Inlet 7'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'B', 'isocratic hold': ' '},
            'Pre-Equilibration': {'inlet': ['Closed', 'Inlet 7'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'B', 'isocratic hold': ' '}
        }
    elif 'Chromatography' in selected_unitOperation:
        default_qd_map = {
            'Pre Sanitization': {'inlet': ['Closed', 'Inlet 4'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'B', 'isocratic hold': ' '},
            'Pre Sanitization 2': {'inlet': ['Closed', 'Inlet 6'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'B', 'isocratic hold': ' '},
            'Pre-Equilibration': {'inlet': ['Closed', 'Inlet 7'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'B', 'isocratic hold': ' '},
            'Equilibration': {'inlet': ['Inlet 1', 'Inlet 7'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'AB', 'isocratic hold': ' '},
            'Charge': {'inlet': ['Sample', 'Closed'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'A', 'isocratic hold': ' '},
            'Wash 1': {'inlet': ['Inlet 1', 'Inlet 7'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'AB', 'isocratic hold': ' '},
            'Wash 2': {'inlet': ['Inlet 1', 'Inlet 7'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'AB', 'isocratic hold': ' '},
            'Wash 3': {'inlet': ['Inlet 1', 'Inlet 7'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'AB', 'isocratic hold': ' '},
            'Elution': {'inlet': ['Inlet 1', 'Inlet 7'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'AB', 'isocratic hold': ' '},
            'Regeneration': {'inlet': ['Inlet 1', 'Inlet 7'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'AB', 'isocratic hold': ' '},
            'Post Sanitization': {'inlet': ['Closed', 'Inlet 4'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'B', 'isocratic hold': ' '},
            'Post Sanitization 2': {'inlet': ['Closed', 'Inlet 4'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'B', 'isocratic hold': ' '},
            'Storage': {'inlet': ['Closed', 'Inlet 5'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'B', 'isocratic hold': ' '}, 
            'Storage Rinse': {'inlet': ['Inlet 1', 'Closed'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'A', 'isocratic hold': ' '},   
            'Pre Sanitization Rinse': {'inlet': ['Inlet 1', 'Closed'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'A', 'isocratic hold': ' '},
            'Pre Sanitization Rinse 2': {'inlet': ['Inlet 1', 'Closed'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'A', 'isocratic hold': ' '},
            'Post Sanitization Rinse 2': {'inlet': ['Inlet 1', 'Closed'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'A', 'isocratic hold': ' '},
            'Post Sanitization Rinse': {'inlet': ['Inlet 1', 'Closed'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'A', 'isocratic hold': ' '},
        }
    else:
        default_qd_map = {
            'Equilibration': {'inlet': ['Inlet 1'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'A', 'isocratic hold': ' '},
            'Elution': {'inlet': ['Inlet 2'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'A', 'isocratic hold': ' '},
            'Wash 1': {'inlet': ['Inlet 3'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'A', 'isocratic hold': ' '},
            'Wash 3': {'inlet': ['Inlet 3'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'A', 'isocratic hold': ' '},
            'Charge': {'inlet': ['Sample'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'A', 'isocratic hold': ' '},
            'Storage': {'inlet': ['Inlet 5'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'B', 'isocratic hold': ' '},
            'Regeneration': {'inlet': ['Inlet 6'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'B', 'isocratic hold': ' '},
            'Pre Sanitization': {'inlet': ['Inlet 4'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'A', 'isocratic hold': ' '},
            'Pre Sanitization Rinse': {'inlet': ['Inlet 1'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'A', 'isocratic hold': ' '},
            'Post Sanitization': {'inlet': ['Inlet 4'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'B', 'isocratic hold': ' '},
            'Post Sanitization Rinse': {'inlet': ['Inlet 1'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'A', 'isocratic hold': ' '},
            'Pre Sanitization 2': {'inlet': ['Inlet 6'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'A', 'isocratic hold': ' '},
            'Pre Sanitization Rinse 2': {'inlet': ['Inlet 1'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'A', 'isocratic hold': ' '},
            'Post Sanitization 2': {'inlet': ['Inlet 6'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'B', 'isocratic hold': ' '},
            'Post Sanitization Rinse 2': {'inlet': ['Inlet 1'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'A', 'isocratic hold': ' '},
            'Storage Rinse': {'inlet': ['Inlet 1'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'A', 'isocratic hold': ' '},
            'Wash 2': {'inlet': ['Inlet 7'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'B', 'isocratic hold': ' '},
            'Pre-Equilibration': {'inlet': ['Inlet 7'], 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' ', 'pump': 'B', 'isocratic hold': ' '}
        }


    with st.expander(f"Default Settings"):
        col1, col2 = st.columns(2)
        with col1:
            uvSetting = st.text_input(
                "Post Charge Wash UV",
                value=3.0,
                key="washUV",
                disabled=PFC_not_uploaded
            )
        with col2:
            wavelengthSetting = st.text_input(
                "UV Detector Wavelength (nm)",
                value=280,
                key="uvWavelength",
                disabled=PFC_not_uploaded
            )


    st.header("Verify Column Parameters")
    
    column_params = {'columnHeight': '', "columnDiameter":'', "contactTime": ''}

    col1, col2, col3 = st.columns(3)
    with col1:
        column_params['columnHeight'] = st.text_input(
            "Column Bed Height",
            value=column_params['columnHeight'],
            key="columnHeight",
            disabled=PFC_not_uploaded
        )
    with col2:
        column_params['columnDiameter'] = st.text_input(
            "Column Diameter",
            value=column_params['columnDiameter'],
            key="diameter",
            disabled=PFC_not_uploaded
        )
    with col3:
        column_params['contactTime'] = st.text_input(
            "Contact Time",
            value=column_params['contactTime'],
            key="time",
            disabled=PFC_not_uploaded
        )

    compensation_factors = {
        "LHM 4250": {"2 mm CF": 4.45, "5 mm CF": 1.94, "skid_size": "3/8"},
        "LHM 4260": {"2 mm CF": 4.71, "5 mm CF": 1.98, "skid_size": "3/8"},
        "LHM 4270": {"2 mm CF": 4.71, "5 mm CF": 1.97, "skid_size": "1/2"},
        "LHM 4280": {"2 mm CF": 4.95, "5 mm CF": 2.02, "skid_size": "1/2"},
        "LHM 4290": {"2 mm CF": 4.89, "5 mm CF": 2.01, "skid_size": "1/2"},
        "LHM 4300": {"2 mm CF": 4.83, "5 mm CF": 2.00, "skid_size": "1/2"},
        "LHM 4310": {"2 mm CF": 4.83, "5 mm CF": 2.00, "skid_size": "1/2"},
        "LHM 4320": {"2 mm CF": 4.50, "5 mm CF": 1.96, "skid_size": "3/4"},
        "LHM 4330": {"2 mm CF": 4.71, "5 mm CF": 1.91, "skid_size": "3/4"},
        "LHM 4340": {"2 mm CF": 4.60, "5 mm CF": 1.99, "skid_size": "3/4"},
        "LHM 4350": {"2 mm CF": 4.92, "5 mm CF": 2.08, "skid_size": "3/4"},
    }

    st.header("Verify Skid Details")

    gradCartOptions = ["LHM 4250", "LHM 4260", "LHM 4270", "LHM 4280", "LHM 4290", "LHM 4300", "LHM 4310", "LHM 4320", "LHM 4330", "LHM 4340", "LHM 4350"]
    cfOptions = ["2 mm CF", "5 mm CF"]
    gradSkidSizeOptions = ["3/8", "1/2", "3/4"]
    col1, col2, col3 = st.columns(3)
    with col1:
        gradientCartSetting = st.selectbox("Gradient Cart",
                        gradCartOptions,
                        key="gradCart",
                        index = gradCartOptions.index("LHM 4250"),
                        disabled=PFC_not_uploaded
                    )
    with col2:
        compFactorSetting = st.selectbox("Compensation Factor Setting",
                        cfOptions,
                        key="compFactor",
                        index=cfOptions.index("2 mm CF"),
                        disabled=PFC_not_uploaded
                    )
    with col3:
        #st.markdown(compensation_factors[gradientCartSetting]['skid_size'])
        skidSizeSetting = compensation_factors[gradientCartSetting]['skid_size']

        skidSize = st.text_input("Skid Size",
                value=skidSizeSetting,
                key="skidSize",
                disabled=True
            )
    
    try:
        compFactor = compensation_factors[gradientCartSetting][compFactorSetting]
    except:
        compFactor = ''
      
    
    st.header("Verify Number of Mainstreams and Cycles")
    col1, col2 = st.columns(2)
    with col1:
        numMS = st.text_input("Number of Mainstreams",
                value=0,
                key="numMS",
                disabled=PFC_not_uploaded
            )
    with col2:
        numCycles = st.text_input("Number of Cycles",
                value=0,
                key="numCycles",
                disabled=PFC_not_uploaded
            )
    try:    
        if int(numCycles)!=0 and int(numMS)!=0 and int(numCycles)%int(numMS)!=0:
            st.error("Expected the number of cycles to be divisible by number of mainstreams, please double check this")
    except:
        st.error("Number of cycles or number of mainstream input format is incorrect. Please doble check that these are integer values with no special characters.")

        
    
    columnParamsIncomplete = True
    for key in column_params.keys():
        if column_params[key].strip() =='':
            columnParamsIncomplete = True
        else:
            columnParamsIncomplete = False

    
    inputs_disabled = PFC_not_uploaded or columnParamsIncomplete 
    
    def fill_default_sample_map(default_qd_map, column_params, pfcQDMap, unitOP):
        if pfcQDMap:
            for i in default_qd_map.keys():
                if i in parameters_in_pfc:
                
                    qdAssignment = pfcQDMap.get(i).get('composition')
                    directionAssignment = pfcQDMap.get(i).get('direction')
                    residenceAssignment =  pfcQDMap.get(i).get('residenceTime')
                    cvAssignment =  pfcQDMap.get(i).get('CV')
                    if "Protein A Capture Chromatography" in unitOP:
                        if pfcQDMap.get(i).get('velocity').strip() =='':
                            if 'sani' in i.lower():
                                try:
                                    velocityAssignment = round(calc_LFlow(float(column_params['columnHeight']), float(column_params['columnDiameter']), float(column_params['contactTime']))["linearFlow"])
                                except: 
                                    velocityAssignment =  pfcQDMap.get(i).get('velocity')
                            elif ('charge' in i.lower() or 'wash 1' in i.lower()) and residenceAssignment.isdigit() and pfcQDMap.get(i).get('velocity').strip() == '':
                                try:
                                    velocityAssignment = round(calc_LFlow_from_residence_time(float(column_params['columnHeight']), float(residenceAssignment)))
                                except: 
                                    velocityAssignment =  pfcQDMap.get(i).get('velocity')
                            else:
                                velocityAssignment =  pfcQDMap.get(i).get('velocity')
                        else:
                            velocityAssignment =  pfcQDMap.get(i).get('velocity')
                    else:
                        velocityAssignment =  pfcQDMap.get(i).get('velocity')

                    default_qd_map[i]['qd'] = qdAssignment
                    default_qd_map[i]['flow_rate'] = velocityAssignment
                    default_qd_map[i]['direction'] = directionAssignment
                    default_qd_map[i]['residence time'] = residenceAssignment
                    default_qd_map[i]['CV'] = cvAssignment
                    default_qd_map[i]['isocratic hold'] = pfcQDMap.get(i).get('isocratic hold')
    
        return default_qd_map
    
    if not inputs_disabled:
        default_qd_map =fill_default_sample_map(default_qd_map, column_params, pfcQDMap, selected_unitOperation)
    
    st.header("Verify Inlet Parameters")

    # Create columns for Pump A/B Inlets
    
    directOptions = ['Downflow', 'Upflow', '']
    requiredBuffers = ['Post Sanitization', 'Equilibration', 'Wash 1', 'Storage']

    requiredBuffersInPFC = [item for item in requiredBuffers if item in parameters_in_pfc]
    
    writeColumns(default_qd_map, requiredBuffersInPFC, inputs_disabled, directOptions, parameters_in_pfc)
    

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
        for buffer in requiredBuffersInPFC:
            if isinstance(default_qd_map[buffer]['qd'], dict):
                for qd in [default_qd_map[buffer]['qd']["Buffer A QD"], default_qd_map[buffer]['qd']["Buffer B QD"]]:
                    if not qd.strip() or not default_qd_map[buffer]['flow_rate'].strip() or not default_qd_map[buffer]['direction'].strip():
                        invalidError.append(f"{buffer} is missing required information")
            elif not default_qd_map[buffer]['qd'].strip() or not default_qd_map[buffer]['flow_rate'].strip() or not default_qd_map[buffer]['direction'].strip():
                        invalidError.append(f"{buffer} is missing required information")
        
        

        values_to_check = [
            (wavelengthSetting, "UV wavelength", float), 
            (uvSetting, "Post charge wash UV", float), 
            (numCycles, "number of cycles", int),
            (numMS, "number of mainstreams", int)
        ]

        for value, error_msg, typefunc in values_to_check:
            try:
                typefunc(value)
            except:
                invalidError.append(f"Incorrect format for {error_msg}.")


        incorrect_column_params = []

        for key in column_params:
            value = column_params.get(key)
            try:
                float(value)
            except:
                incorrect_column_params.append(value)

        if len(incorrect_column_params)>1:
            invalidError.append(f"Incorrect column parameters detected, {', '.join(incorrect_column_params)} are invalid inputs")
        elif len(incorrect_column_params)==1:
            invalidError.append(f"Incorrect column parameter detected, {''.join(incorrect_column_params)} is an invalid input")



        # Check QD format for all fields that have values
        for buffer in default_qd_map.keys():
            if isinstance(default_qd_map[buffer]['qd'], dict):
                for qd in [default_qd_map[buffer]['qd']["Buffer A QD"], default_qd_map[buffer]['qd']["Buffer B QD"]]:
                    if qd.strip() and not is_valid_qd(qd):
                        invalidError.append(f"Invalid QD format for {buffer}. Format should be 'QD' followed by 5 digits (e.g., QD00015)")
            elif default_qd_map[buffer]['qd'].strip() and not is_valid_qd(default_qd_map[buffer]['qd']):
                        invalidError.append(f"Invalid QD format for {buffer}. Format should be 'QD' followed by 5 digits (e.g., QD00015)")
            try:
                float(default_qd_map[buffer]['flow_rate'])
            except:
                if default_qd_map[buffer]['flow_rate'].strip():
                    invalidError.append(f"Expected flow rate to be a number for {buffer}. (e.g., 300)")

            try:
                float(default_qd_map[buffer]['CV'])
            except:
                if default_qd_map[buffer]['CV'].strip():
                    invalidError.append(f"Expected CV to be a number for {buffer}. (e.g., 2)")

            try:
                float(default_qd_map[buffer]['residence time'])
            except:
                if default_qd_map[buffer]['residence time'].strip() and default_qd_map[buffer]['residence time']!="--":
                    invalidError.append(f"Expected residence time to be a number or -- for {buffer}. (e.g., 30, --)")

            try:
                float(default_qd_map[buffer]['isocratic hold'])
            except:
                if default_qd_map[buffer]['isocratic hold'].strip():
                    invalidError.append(f"Expected isocratic hold to be a number for {buffer}. (e.g., 3,)")
        
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
        'number_of_MS': numMS, 
        'number_of_cycles': numCycles, 
        'UV_detection_wavelength': wavelengthSetting, 
        'post_wash_UV': uvSetting, 
        'scouting_blocks_included': parameters_in_pfc,
        'compensation_factor': compFactor,
        'skid_size': skidSizeSetting
    }