
# importing required classes
from pypdf import PdfReader
from difflib import SequenceMatcher

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
    
    return best_match


def extract_text_from_pdf(pdfPath, outputFilePath):
# creating a pdf reader object
    reader = PdfReader(pdfPath)
    with open(outputFilePath+'.txt', 'w') as file:
        for i in range(len(reader.pages)):
            page = reader.pages[i]
            file.write(page.extract_text())
            file.write('\n')

    return outputFilePath+'.txt'

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

                    return closest_match_unit_op(methodUnitOp, options)