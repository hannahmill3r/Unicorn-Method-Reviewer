import fitz  # PyMuPDF

def annotate_doc(unannotatedDoc, outfileName, highlights):
    # Open the PDF
    #pdf_document = fitz.open("v001 scouting method LB2273 ProA.pdf")
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
                #highlight_rect.set_colors(stroke=(1, 0, 0))
                annot = page.add_highlight_annot(highlight_rect)
                annot.set_colors(stroke=(0.6, 0.8, 1))
                annot.update()


    # Save the modified PDF
    pdf_document.save(outfileName)
    pdf_document.close()

    return outfileName
