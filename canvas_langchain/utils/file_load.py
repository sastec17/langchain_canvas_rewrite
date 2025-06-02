import tempfile
from langchain.docstore.document import Document
from canvas_langchain.utils.common import format_data
from canvas_langchain.utils.embedded_media import parse_html_for_text_and_urls
from typing import List

from langchain_community.document_loaders import (
    Docx2txtLoader,
    UnstructuredExcelLoader,
    UnstructuredMarkdownLoader,
    UnstructuredPowerPointLoader,
    UnstructuredURLLoader
) 

# TODO: INCORPORATE FORMAT_DATA? 
def load_rtf_or_text_file(file) -> List[Document]:
    """Loads and formats text and rtf file data"""
    file_contents = file.get_contents(binary=False)
    text_document = Document(page_content=file_contents,
                             metadata={"filename": file.filename, 
                                       "source": file.url, 
                                       "kind": "file",
                                       "file_id": file.id })
    return [text_document]

def load_html_file(file, loader) -> List[Document]:
    # NEEDS CANVAS AND 
    file_contents = file.get_contents(binary=False)
    (file_text, embed_urls) = parse_html_for_text_and_urls(canvas=loader.canvas,
                                                           course=loader.course,
                                                           html=file_contents)
    metadata={"content":file_text,
              "data": {"name": file.filename,
                       "source":file.url,
                       "kind":"file",
                       "id": file.id}
                }
    return format_data(metadata=metadata, embed_urls=embed_urls)

def load_pdf_file():
    return

def load_file_general(file, file_type, base_api):
    """Loads docx, excel, pptx, and md files"""
    file_contents = file.get_contents(binary=True)
    docs=[]
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = f"{temp_dir}/{file.filename}"

        with open(file_path, "wb") as binary_file:
            # Write bytes to file
            binary_file.write(file_contents)

        match file_type:
            case '.csv':
                loader = UnstructuredExcelLoader(file_path)
            case '.docx':
                loader=Docx2txtLoader(file_path)
            case '.md':
                loader = UnstructuredMarkdownLoader(file_path)
            case '.pptx':
                loader=UnstructuredPowerPointLoader(file_path)

        docs = loader.load()

        for i, _ in enumerate(docs):
            docs[i].metadata["filename"] = file.filename
            docs[i].metadata["source"] = f"{base_api}/files/{file.id}"

    return docs