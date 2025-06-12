import streamlit as st
#from blockNameDict import blockNameDictionary
import pandas as pd
import json

blockNameDictionary = {
        'Equilibration': 'Equilibration',
        'Elution': 'Elution',
        'Wash_1': 'Wash 1',
        'Col_Wash_1': 'Wash 1',
        'Wash_3': 'Wash 3',
        'Col_Wash_3': 'Wash 3',
        'Charge': 'Charge',
        'Storage': 'Storage',
        'Regeneration': 'Regeneration',
        'Regen': 'Regeneration',
        'Col_Regen': 'Regeneration',
        'Pre_Sanitization': 'Pre Sanitization',
        'Pre_Sani_Rinse':'Pre Sanitization Rinse',
        'Rinse_1':'Post Sanitization Rinse',
        'Rinse_2': 'Post Sanitization Rinse 2',
        'Post_Use_Sanitization': 'Post Sanitization',
        'Post_Use_Sani': 'Post Sanitization',
        'Pre_Use_Sani': 'Pre Sanitization',
        'Clean_1': 'Post Sanitization',
        'Clean_2': 'Post Sanitization',
        'Rinse_3': 'Post Sanitization Rinse',
        'Rinse_4': 'Post Sanitization Rinse 2',
        'Storage_Rinse': 'Storage Rinse',
        'Wash_2': 'Wash 2',
        'Col_Wash_2': 'Wash 2',
        'Pre_Use_Clean_1': 'Pre Sanitization',
        'Pre_Use_Clean_2': 'Pre Sanitization 2',
        'Pre_Use_Rinse_1' :'Pre Sanitization Rinse', 
        'Pre_Use_Rinse_2' :'Pre Sanitization Rinse 2', 
        'first_cv_equil_flowrate': "Pre Sanitization Rinse", 
        'Flush_Skid_Inlet_2_Elution': "Elution", 
        'Wash_2_System_Flush': "Wash 2", 
        'High_Salt_Wash': 'Regeneration',
        'Post_Charge_Wash': 'Wash 1',
        'Post_Charge_Wash2': 'Wash 2',
        'Post_Charge_Wash3': 'Wash 3',
        'Pre_Equilibration': 'Pre-Equilibration', 
        'MabSelect_Equilibration': 'Equilibration', 
        'Equil': 'Equilibration',
        'Pre-Equil': 'Pre-Equilibration', 
        'Pre_Sani': 'Pre Sanitization',
        'Post_Sani': 'Post Sanitization',
        'Post_Use_column_Sanitization': 'Post Sanitization',
        'Pre_Use_column_Sanitization': 'Pre Sanitization',


    }

#TODO: this is hard coded but I would love to have it accessable in the UI so that if any changes to the methoid are made it could be easily changed without changing the code.
ValidatedblockNameDictionary = {}

def show_block_name():
    blockName_df = pd.DataFrame(list(blockNameDictionary.items()), columns=['Unicorn Method Terminology', 'PFC Terminology'])
    with st.sidebar:
        with st.expander("Verify the Block name list 📋"):
            user_validate_df = st.data_editor(blockName_df,use_container_width=True,num_rows="dynamic",key="verify_list_editor")
            #ValidatedblockNameDictionary = user_validate_df.to_dict(orient='records')
            validated_button = st.button('Validated')
            if not user_validate_df.equals(blockName_df) and validated_button:
                write_user_validated_blockname(user_validate_df,ValidatedblockNameDictionary)
                st.write('Validated !! ✅')
            elif validated_button:
                write_user_validated_blockname(user_validate_df,ValidatedblockNameDictionary)
                st.write('Validated !! ✅')
            else:
                write_user_validated_blockname(user_validate_df,ValidatedblockNameDictionary)
            

def write_user_validated_blockname(df,validated_dict):
    for rows in df.iterrows():
        row = rows[1]
        if row['Unicorn Method Terminology'] != 'null':
            validated_dict[row['Unicorn Method Terminology']] = row['PFC Terminology']
    with open('user_validated_blockName_Dict.json','w') as f:
        json.dump(validated_dict,f,indent=4)
    

def read_user_valided_blockName():
    
    with open('user_validated_blockName_Dict.json', 'r') as file:
        # Load its content and 
        block_name_dict = json.load(file)
        
    return block_name_dict