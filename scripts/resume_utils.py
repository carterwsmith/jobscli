from pypdf import PdfReader
from docx2python import docx2python

def get_text(filename):
    # if extension is .docx
    if filename.endswith('.docx'):
        return get_docx_text(filename)
    # if extension is .pdf
    elif filename.endswith('.pdf'):
        return get_pdf_text(filename)
    # if extension is .txt
    elif filename.endswith('.txt'):
        return get_file_text(filename)
    else:
        raise Exception("Unsupported file type (docx/pdf/txt)")

def get_pdf_text(filename):
    """Return the text of a PDF file."""
    raw_text = PdfReader(filename).pages[0].extract_text()
    # remove all escaped characters and newlines and tabs
    text = raw_text.encode('ascii', 'ignore').decode().replace("\n", " ").replace("\t", "")
    return text

def get_docx_text(filename):
    """Return the text of a DOCX file."""
    with docx2python(filename) as docx_content:
        raw_text = docx_content.text
        text = raw_text.encode('ascii', 'ignore').decode().replace("\n", " ").replace("\t", "")
        return text

def get_file_text(filename):
    """Return the text of a TXT file."""
    with open(filename, 'r') as f:
        raw_text = f.read()
        text = raw_text.encode('ascii', 'ignore').decode().replace("\n", " ").replace("\t", "")
        return text