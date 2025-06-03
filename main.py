from annotatePDF import annotate_doc
from proAMethodParser import protein_A_method_parser
from blockVerification import check_purge_block_settings, check_watch_settings, check_MS_blocks_settings_pdf, check_column_params, check_indiv_blocks_settings_pdf, check_end_of_run_pdf, check_scouting, calc_LFlow_from_residence_time
from streamlitUI import create_inlet_qd_interface, display_pdf
from extractText import extract_text_from_pdf
import streamlit as st

import os


def main():
    result = create_inlet_qd_interface()

    if result['submit_pressed']:
        st.info("Processing document and comparing QD numbers...")
        
        # Process the PDF and analyze purge blocks
        outputFile = extract_text_from_pdf('tempfile.pdf', 'output2')
       
        with open(outputFile, 'r') as file:
            text = file.read()
            
            # Display results
            st.header("Unicorn Methods Analysis Results")

            # Save uploaded file to disk temporarily
            if result['uploaded_file'] is not None:

                blockData = protein_A_method_parser(text, result)

                highlightsPurge = check_purge_block_settings(blockData["purge_data"], result['inlet_data'], result['skid_size'])
                highlightsMS = check_MS_blocks_settings_pdf(blockData["equilibration_data"], result['inlet_data'], result["number_of_MS"], result['skid_size'])
                highlightsColumnParams = check_column_params(blockData["column_params"], result['column_params'])
                highlightsIndiv = check_indiv_blocks_settings_pdf(blockData["indiv_block_data"], result['inlet_data'], result['column_params'], result['compensation_factor'], result['skid_size'])
                highlightsWatchSettings = check_watch_settings(blockData["watch_block_data"])
                highlightsFinalBlock = check_end_of_run_pdf(blockData["final_block_data"])
                highlightsScouting = check_scouting(blockData["scouting_data"], result['inlet_data'], result['post_wash_UV'], result['number_of_cycles'], result["number_of_MS"], result["scouting_blocks_included"], result['column_params'])

                mergedHighlights = [item for sublist in [highlightsPurge, highlightsScouting, highlightsMS, highlightsColumnParams, highlightsIndiv, highlightsFinalBlock, highlightsWatchSettings] for item in sublist]

                #if the merged highlights list is empty, than there were no incorrect methods settings, otherwise, error
                if not mergedHighlights:
                    st.success("✅ Method settings are correct")
                else:
                    st.error("❌ There were some unexpected settings in the document, please double check them")
                
                annotate_doc('tempfile.pdf', "annotated_example2.pdf", mergedHighlights)

                with st.expander(f"❌ Failed to Purge"):
                    for i in blockData["inlets_not_purged"]:
                        if isinstance(result['inlet_data'].get(i).get('qd'), list):
                            st.write(i + " was not purged with " + ', '.join(result['inlet_data'].get(i).get('qd')))
                        else:
                            st.write(i + " was not purged with " + result['inlet_data'].get(i).get('qd'))
                if blockData['UV_Auto_Zero'] == False:
                    with st.expander(f"❌ Missing UV Auto Zero Block"):
                        st.write("UZ Auto Zero should be turned on for every run.")
                display_pdf("annotated_example2.pdf")

                if os.path.exists('tempfile.pdf'):
                    os.remove('tempfile.pdf')
                    print(f"{'tempfile.pdf'} has been deleted.")
                else:
                    print(f"{'tempfile.pdf'} does not exist.")



     

if __name__ == "__main__":
    main()