from io import BytesIO
import tempfile
from PyPDF2 import PdfReader
from PyPDF2 import errors
from binascii import Error as binasciiError
from typing import List
from urllib.parse import urljoin
from canvas_langchain.base import BaseSectionLoaderVars

from canvas_langchain.base import BaseSectionLoader
from canvasapi.exceptions import CanvasException, ResourceDoesNotExist

from langchain.docstore.document import Document
from canvas_langchain.utils.common import format_data

from langchain_community.document_loaders import (
    Docx2txtLoader,
    UnstructuredExcelLoader,
    UnstructuredMarkdownLoader,
    UnstructuredPowerPointLoader,
    UnstructuredURLLoader
) 


# TODO: Test .md, .excel, .docx file types
class FileLoader(BaseSectionLoader):
    def __init__(self, BaseSectionVars: BaseSectionLoaderVars, course_api, invalid_files):
        super().__init__(BaseSectionVars)
        self.invalid_files = invalid_files
        self.course_api = course_api
        # TODO: REVISE THIS SYSTEM
        self.type_match = {
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" : ".csv",
            "application/vnd.ms-excel": ".csv",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".md",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx"
        }


    def load_files(self) -> List[Document]:
        """Loads and formats all files from Canvas course"""
        file_documents = []
        try:
            # TODO: LOOK INTO NESTED TRY EXCEPTS
            files = self.course.get_files()
            for file in files:
                try: 
                    if f"File:{file.id}" not in self.indexed_items:
                        self.indexed_items.add(f"File:{file.id}")
                        file_documents.extend(self.load_file(file))
                
                # file is in hidden module
                except ResourceDoesNotExist:
                    print("File resourceDNE")

        except CanvasException as error:
            print("Canvas Exception loading files", error)
        return file_documents
    

    def load_file(self, file) -> List[Document]:
        """Loads given file based on extension"""
        file_documents = []
        try:
            content_type = getattr(file, "content-type")

            if content_type in ["text/plain", "text/rtf"]:
                file_documents.extend(self._load_rtf_or_text_file(file))
            elif content_type == "text/html":
                file_documents.extend(self._load_html_file(file))
            elif content_type == "application/pdf":
                file_documents.extend(self._load_pdf_file(file))
            elif content_type in self.type_match:
                file_documents.extend(self._load_file_general(file, 
                                                              self.type_match[content_type]))

        except ResourceDoesNotExist as err:
            print('Test this was hit first', err)
        return file_documents


    def _load_rtf_or_text_file(self, file) -> List[Document]:
        """Loads and formats text and rtf file data"""
        file_contents = file.get_contents(binary=False)
        text_document = Document(page_content=file_contents,
                                metadata={"filename": file.filename, 
                                        "source": file.url, 
                                        "kind": "file",
                                        "file_id": file.id })
        return [text_document]


    def _load_html_file(self, file) -> List[Document]:
        """Loads and formats html file data"""
        file_contents = file.get_contents(binary=False)
        file_text, embed_urls = self.parse_html(html=file_contents)
        metadata={"content":file_text,
                "data": {"name": file.filename,
                        "source":file.url,
                        "kind":"file",
                        "id": file.id}
                    }
        return format_data(metadata=metadata, embed_urls=embed_urls)


    def _load_pdf_file(self, file):
        """Loads given pdf file by page"""
        file_contents = file.get_contents(binary=True)
        docs = []
        try:
            pdf_reader = PdfReader(BytesIO(file_contents))
            # extract info by page
            for i, page in enumerate(pdf_reader.pages):
                pdf_page = Document(page_content=page.extract_text(),
                                    metadata={"filename": file.filename,
                                              "source": urljoin(self.course_api, f"files/{file.id}"),
                                              "kind": "file",
                                              "page": i+1}
                                    )
                docs.append(pdf_page)

        except Exception as err:
            print("PDF EXCEPTION ERROR", err)
        return docs


    def _load_file_general(self, file, file_type):
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
                docs[i].metadata["source"] = urljoin(self.course_api, f"files/{file.id}")

        return docs
