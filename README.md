
# UNICORN Method Validator
A Python-based tool for validating and comparing Process Flow Charts (PFC) against UNICORN chromatography method files.

## Overview
This tool analyzes chromatography methods by:
1. Reading and parsing UNICORN method PDFs
2. Comparing settings against PFC specifications
3. Highlighting discrepancies in the output PDF
4. Validating key parameters like purge sequences, individual blocks, peak protection, and scouting requirements

## Key Features
- PDF text extraction using PyMuPDF (fitz)
- Intelligent block parsing for method components
- Automated validation of:
  - Column parameters
  - block settings: flow rates, QD compositions, Inlet settings, bubbletrap settings, oulet settings and more.
  - Peak protection settings

## Installation
```bash
pip install -r requirements.txt
```

Required packages:
- PyMuPDF (fitz)
- numpy
- re (built-in)
- difflib


## Core Functions

### find_highlight_loc()
Main processing function that:
- Parses PDF document block by block
- Extracts method settings and parameters
- Validates against PFC specifications
- Returns structured validation data


### queryPurgeBlock(), queryIndividualBlocks(), and query_watch()
Maintains consistency of QD mappings across:
- Handed a block of text from the methods document, these functions locate, clean, and return purge block, individual block, and watch block data as needed
- Data is returned in a dictionary format, a purge block example is shown below:

```python
{
    'manflow': float,
    'column_setting': str,
    'outlet_setting': str,
    'bubbletrap_setting': str,
    'inlet_QD_setting': str,
    'inlet_setting': str,
    'end_block_setting': float
}
```


## Data Structures

### Block Data
Each method block is processed within the find_highlight_loc() function and recorded in a dictionary containing:
```python
{
    "blockName": str,      # Block identifier
    "blockPage": int,      # PDF page number
    "location": tuple,     # (x0, y0, x1, y1) coordinates
    "settings": dict       # Block-specific settings
}
```

### Invalid parameter data
Each method parameter that does not match expected output, is recorded in a dictionary with the following format, where block data is the nested 
dictionary described above, and the annotated text is a list of all of the incorrect warning statements associated with that block.
```python
{
    "blockData": dict,
    "annotationText": list
}
```

## Contributing
Please submit issues and pull requests for:
- Bug fixes
- Feature enhancements
- Documentation improvements


This README provides a comprehensive overview of your tool's functionality and usage, based on the main processing loop you shared. You may want to add specific sections for your repository's structure, testing procedures, and any additional features not covered in the main loop.
