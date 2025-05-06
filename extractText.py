
# importing required classes
from pypdf import PdfReader
from difflib import SequenceMatcher
import fitz

def closest_match_unit_op(search_string, string_array):
    # Initialize variables to track best match
    best_ratio = 0
    best_match = None
    
    # Convert search string to lowercase for case-insensitive matching
    search_string = search_string.lower()
    
    # Compare search string with each string in array
    for candidate in string_array:
        # Convert candidate to lowercase for comparison
        candidate_lower = candidate.lower()
        
        # Calculate similarity ratio
        ratio = SequenceMatcher(None, search_string, candidate_lower).ratio()
        
        # Update best match if current ratio is higher
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = candidate
    
    return best_match, best_ratio



def extract_text_from_pdf(pdf_path, output_file_path):
    """
    Extract text from the PDF and save it to a text file, preserving indentation.
    
    Args:
        pdf_path (str): Path to the PDF file
        output_file_path (str): Path to the output text file (without extension)
        
    Returns:
        str: Path to the output text file
    """
    # Open the PDF file
    doc = fitz.open(pdf_path)
    
    # Open the output text file for writing
    with open(output_file_path + '.txt', 'w') as file:
        # Iterate through each page in the PDF
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text("text")  # Extract text with indentation
            
            # Write the extracted text to the file
            file.write(text)
            file.write('\n')
    
    return output_file_path + '.txt'


def extract_unit_opertaion_from_method(outputFile, options):
    # Split the text into lines
    with open(outputFile, 'r') as file:
        text = file.read()
        lines = text.split('\n')
        
        
        # Look for method content
        for line in lines:
            # Start capturing after seeing "Main method:"
            if "Method: " in line:
                clean_line = line.strip()
                if clean_line:
                    methodUnitOp = ' '.join(clean_line.split()[5:])
                    match, ratio = closest_match_unit_op(methodUnitOp, options)
                    return match