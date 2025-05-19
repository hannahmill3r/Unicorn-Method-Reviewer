import fitz  # PyMuPDF


def annotate_doc(unannotatedDoc, outfileName, highlights):
    """
    A utility function that adds annotation markers and highlights to a PDF document.
    Takes an unannotated PDF and adds:
    - Text annotations with error messages in the right margin
    - Blue highlight boxes around the problematic text areas
    - Saves the annotated version to a new file

    Args:
        unannotatedDoc: Path to input PDF file
        outfileName: Path for saving annotated PDF 
        highlights: List of highlight objects containing location and annotation text
    """
    # Open the PDF
    pdf_document = fitz.open(unannotatedDoc)

    # Add a text annotation
    for pageNum in range(len(pdf_document)):

        for highlight in highlights:
            if pageNum+1 == int(highlight['blockData']['blockPage']):
                page = pdf_document[pageNum]
                point = fitz.Point(page.rect.width - 25, highlight['blockData']["location"][1])
                textAnnot = page.add_text_annot(point, '\n'.join(highlight["annotationText"]), icon='Help')
                textAnnot.set_colors(stroke=(0, 0, 0))
                textAnnot.update()

                #Add a highlight
                highlight_rect = fitz.Rect(highlight['blockData']["location"][0], highlight['blockData']["location"][1], highlight['blockData']["location"][2], highlight['blockData']["location"][3])  # x0, y0, x1, y1
               
                annot = page.add_highlight_annot(highlight_rect)
                annot.set_colors(stroke=(0.6, 0.8, 1))
                annot.update()


    # Save the modified PDF
    pdf_document.save(outfileName)
    pdf_document.close()

    return outfileName
