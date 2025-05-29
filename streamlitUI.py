import streamlit as st
from extractText import extract_text_from_pdf
from extractPFCData import output_PFC_params
from extractText import extract_unit_opertaion_from_method
import base64
import tempfile
import fitz
import re
from flowCalculations import calc_LFlow, calc_LFlow_from_residence_time

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

def writeColumns(default_qd_map, requiredBuffers, inputs_disabled, directOptions, parameters_in_pfc):
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
                        index=directOptions.index(default_qd_map[buffer].get(key).strip()),
                        disabled=inputs_disabled
                    )
                elif key == 'qd' and parse_gradient_composition(default_qd_map[buffer].get(key)):
                    parsed_gradient = parse_gradient_composition(default_qd_map[buffer].get(key))

                    col5, col6 = st.columns(2)
                    default_qd_map[buffer][key] = [0, 0]
                    
                    with col5:
                        default_qd_map[buffer][key][0] = st.text_input(
                            label,
                            value=parsed_gradient['Buffer A']['QD'],
                            help = f"Buffer A: {parsed_gradient['Buffer A']['percent']}% {parsed_gradient['Buffer A']['QD']}",
                            key=field_key + "Buffer A",
                            disabled=inputs_disabled
                        )

                        
                    with col6:
                        default_qd_map[buffer][key][1] = st.text_input(
                            label,
                            value=parsed_gradient['Buffer B']['QD'],
                            help = f"Buffer B: {parsed_gradient['Buffer B']['percent']}% {parsed_gradient['Buffer B']['QD']}",
                            key=field_key + "Buffer B",
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
        if buffer in parameters_in_pfc:
            create_buffer_inputs(buffer, default_qd_map[buffer].get('inlet'))

    # Process Pump B Inlets
    st.subheader("Pump B Inlets")
    pump_b_buffers = ['Post Sanitization', 'Post Sanitization Rinse', 'Storage', 'Regeneration', 'Wash 2']
    for buffer in pump_b_buffers:
        if buffer in parameters_in_pfc:
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
        'About': "The Unicorn Method reviewer takes a dPFC document and parses a specified unit operation. The output is compared against the values described in the provided scouting method's document, highlighting possible transcription errors.",
        'Get help': "mailto:Hannah.miller@lilly.com"
    }
)
    st.title("UNICORN Method Validator")

    uploaded_file = st.file_uploader("Upload UNICORN Method PDF", type="pdf")
    uploaded_PFC_file = None
    outputFile = None

    options = ['None', 'Detergent Viral Inactivation', 'Hydrophobic Interaction Chromatography', 'Protein A Capture Chromatography', 
               'Low pH Viral Inactivation and Clarification', 'Cation Exchange Chromatography', 
               'Viral Filtration', 'Tangential Flow Filtration', 
               'Intermediate Drug Substance Dispensing and Storage']
    
    
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

        options = ['Detergent Viral Inactivation', 'Hydrophobic Interaction Chromatography', 'Protein A Capture Chromatography',
                  'Low pH Viral Inactivation and Clarification', 'Cation Exchange Chromatography',
                  'Viral Filtration', 'Tangential Flow Filtration',
                  'Intermediate Drug Substance Dispensing and Storage']
        
        outputFile = extract_text_from_pdf('tempfile.pdf', 'output2')
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
    
    PFC_not_uploaded = uploaded_PFC_file is None
    saniStrategyOptions = ["PrismA", "SuRe"]
    if not PFC_not_uploaded:
            pfcQDMap, saniStrategy, parameters_in_pfc = output_PFC_params(uploaded_PFC_file, selected_option)
            if not pfcQDMap:
                st.write(f"❌ Could not find specified unit operation, please make sure this is a word document dPFC.")

            selectedSaniStrategy = st.selectbox('Verify Sanitatization Strategy:', saniStrategyOptions, 
                                        index=saniStrategyOptions.index(saniStrategy), disabled=False)
    else:
        saniStrategyOptions = ['None']
        selectedSaniStrategy = st.selectbox('Verify Sanitatization Strategy:', saniStrategyOptions, 
                                     index=saniStrategyOptions.index('None'), disabled=True)
        st.info("Please upload PFC before specifying sanitization strategy")

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
        'Pre Sanitization 2': {'inlet': 'Inlet 6', 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' '},
        'Pre Sanitization Rinse 2': {'inlet': 'Inlet 1', 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' '},
        'Post Sanitization 2': {'inlet': 'Inlet 6', 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' '},
        'Post Sanitization Rinse 2': {'inlet': 'Inlet 1', 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' '},
        'Storage Rinse': {'inlet': 'Inlet 1', 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' '},
        'Wash 2': {'inlet': 'Inlet 7', 'qd': ' ', 'flow_rate': ' ', 'direction': ' ', 'residence time': ' ', 'CV': ' '}
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
        "LHM 4250": {"2 mm CF": 4.45, "5 mm CF": 1.94},
        "LHM 4260": {"2 mm CF": 4.71, "5 mm CF": 1.98},
        "LHM 4270": {"2 mm CF": 4.71, "5 mm CF": 1.97},
        "LHM 4280": {"2 mm CF": 4.95, "5 mm CF": 2.02},
        "LHM 4290": {"2 mm CF": 4.89, "5 mm CF": 2.01},
        "LHM 4300": {"2 mm CF": 4.83, "5 mm CF": 2.00},
        "LHM 4310": {"2 mm CF": 4.83, "5 mm CF": 2.00},
        "LHM 4320": {"2 mm CF": 4.50, "5 mm CF": 1.96},
        "LHM 4330": {"2 mm CF": 4.71, "5 mm CF": 1.91},
        "LHM 4340": {"2 mm CF": 4.60, "5 mm CF": 1.99},
        "LHM 4350": {"2 mm CF": 4.92, "5 mm CF": 2.08}
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
        skidSizeSetting = st.selectbox("Gradient Skid Size",
                        gradSkidSizeOptions,
                        key="skidSize",
                        index=gradSkidSizeOptions.index("3/4"),
                        disabled=PFC_not_uploaded
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
        
    if int(numCycles)!=0 and int(numMS)!=0 and int(numCycles)%int(numMS)!=0:
        st.error("Expected the number of cycles to be divisible by number of mainstreams, please double check this")
        
    
    columnParamsIncomplete = True
    for key in column_params.keys():
        if column_params[key].strip() =='':
            columnParamsIncomplete = True
        else:
            columnParamsIncomplete = False

    inputs_disabled = uploaded_PFC_file is None or columnParamsIncomplete
    def fill_default_sample_map(default_qd_map, column_params, pfcQDMap):

        if pfcQDMap:
            for i in default_qd_map.keys():
                
                qdAssignment = pfcQDMap.get(i).get('composition')
                directionAssignment = pfcQDMap.get(i).get('direction')
                residenceAssignment =  pfcQDMap.get(i).get('residenceTime')
                cvAssignment =  pfcQDMap.get(i).get('CV')
                if pfcQDMap.get(i).get('velocity').strip() == '':
                    if 'sani' in i.lower():
                        try:
                            velocityAssignment = round(calc_LFlow(float(column_params['columnHeight']), float(column_params['columnDiameter']), float(column_params['contactTime']))["linearFlow"])
                        except: 
                            velocityAssignment =  pfcQDMap.get(i).get('velocity')
                    elif 'charge' in i.lower() or 'wash 1' in i.lower() and residenceAssignment.isdigit():
                        try:
                            velocityAssignment = round(calc_LFlow_from_residence_time(float(column_params['columnHeight']), float(residenceAssignment)))
                        except: 
                            velocityAssignment =  pfcQDMap.get(i).get('velocity')
                else:
                    velocityAssignment =  pfcQDMap.get(i).get('velocity')

                default_qd_map[i]['qd'] = qdAssignment
                default_qd_map[i]['flow_rate'] = velocityAssignment
                default_qd_map[i]['direction'] = directionAssignment
                default_qd_map[i]['residence time'] = residenceAssignment
                default_qd_map[i]['CV'] = cvAssignment
    
        return default_qd_map
    
    if not inputs_disabled:
        default_qd_map =fill_default_sample_map(default_qd_map, column_params, pfcQDMap)

    st.header("Verify Inlet Parameters")


    # Create columns for Pump A Inlets
    st.subheader("Pump A Inlets")
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
            if isinstance(default_qd_map[buffer]['qd'], list):
                for qd in default_qd_map[buffer]['qd']:
                    if not qd.strip() or not default_qd_map[buffer]['flow_rate'].strip() or not default_qd_map[buffer]['direction'].strip():
                        invalidError.append(f"{buffer} is missing required information")
            elif not default_qd_map[buffer]['qd'].strip() or not default_qd_map[buffer]['flow_rate'].strip() or not default_qd_map[buffer]['direction'].strip():
                        invalidError.append(f"{buffer} is missing required information")

                

        # Check QD format for all fields that have values
        for buffer in default_qd_map.keys():
            if isinstance(default_qd_map[buffer]['qd'], list):
                for qd in default_qd_map[buffer]['qd']:
                    if qd.strip() and not is_valid_qd(qd):
                        invalidError.append(f"Invalid QD format for {buffer}. Format should be 'QD' followed by 5 digits (e.g., QD00015)")
            elif default_qd_map[buffer]['qd'].strip() and not is_valid_qd(default_qd_map[buffer]['qd']):
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
        'number_of_MS': numMS, 
        'number_of_cycles': numCycles, 
        'UV_detection_wavelength': wavelengthSetting, 
        'post_wash_UV': uvSetting, 
        'scouting_blocks_included': parameters_in_pfc,
        'compensation_factor': compFactor,
        'skid_size': skidSizeSetting
    }



