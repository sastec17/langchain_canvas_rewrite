import tempfile
from io import BytesIO
from PyPDF2 import PdfReader
from PyPDF2 import errors
from typing import List
from urllib.parse import urljoin
from canvas_langchain.base import BaseSectionLoaderVars

from canvas_langchain.base import BaseSectionLoader
from canvasapi.exceptions import CanvasException, ResourceDoesNotExist

from langchain.docstore.document import Document

from langchain_community.document_loaders import (
    Docx2txtLoader,
    UnstructuredExcelLoader,
    UnstructuredMarkdownLoader,
    UnstructuredPowerPointLoader,
    CSVLoader
) 

class FileLoader(BaseSectionLoader):
    def __init__(self, BaseSectionVars: BaseSectionLoaderVars, course_api, invalid_files):
        super().__init__(BaseSectionVars)
        self.invalid_files = invalid_files
        self.course_api = course_api
        self.type_match = {
            "text/md": "md",
            "text/csv": "csv",
            "application/vnd.ms-excel": "excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" : "excel",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx"
        }


    def load_files(self) -> List[Document]:
        """Loads and formats all files from Canvas course"""
        self.logger.info("Loading files...")
        file_documents = []
        try:
            files = self.course.get_files()
            for file in files:
                file_documents.extend(self.load_file(file))

        except CanvasException as error:
            self.logger.error("Canvas Exception loading files", error)
        exit()
        return file_documents
    

    def load_file(self, file) -> List[Document]:
        """Loads given file based on extension"""
        if f"File:{file.id}" not in self.indexed_items:
            self.indexed_items.add(f"File:{file.id}")
            try:
                content_type = getattr(file, "content-type")

                if content_type in ["text/plain", "text/rtf"]:
                    return self._load_rtf_or_text_file(file)
                elif content_type == "text/html":
                    return self._load_html_file(file)
                elif content_type == "application/pdf":
                    return self._load_pdf_file(file)
                elif content_type in self.type_match:
                    return self._load_file_general(file, self.type_match[content_type])
            
            # exception occurs when file is in a hidden module
            except ResourceDoesNotExist as err:
                self.logger.error("File %s does not exist - likely in hidden module %s", file.filename, err)
                file_content_type = getattr(file, "content-type")
                self.invalid_files.append(f"{file.filename} ({file_content_type})")
        return []


    def _load_rtf_or_text_file(self, file) -> List[Document]:
        """Loads and formats text and rtf file data"""
        self.logger.debug("Loading rtf or txt file: %s", file.filename)
        file_contents = file.get_contents(binary=False)
        text_document = Document(page_content=file_contents,
                                metadata={"filename": file.filename, 
                                        "source": file.url, 
                                        "kind": "file",
                                        "file_id": file.id })
        return [text_document]


    def _load_html_file(self, file) -> List[Document]:
        """Loads and formats html file data"""
        self.logger.debug("Loading html file: %s", file.filename)
        file_contents = file.get_contents(binary=False)
        file_text, embed_urls = self.parse_html(html=file_contents)
        metadata={"content":file_text,
                "data": {"name": file.filename,
                        "source":file.url,
                        "kind":"file",
                        "id": file.id}
                    }
        return self.format_data(metadata=metadata, embed_urls=embed_urls)


    def _load_pdf_file(self, file):
        """Loads given pdf file by page"""
        self.logger.debug("Loading pdf file: %s", file.filename)
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
        #TODO: binascii error handling needed? 
        except errors.FileNotDecryptedError as err:
            self.logger.error("Error: pdf %s is encrypted. Error: %s", file.filename, err)
        except Exception as err:
            self.logger.error("Error loading pdf %s. Error: %s", file.filename, err)
        return docs


    def _load_file_general(self, file, file_type):
        """Loads docx, excel, pptx, and md files"""
        self.logger.debug("Loading %s file: %s", file_type, file.filename)
        file_contents = file.get_contents(binary=True)
        docs=[]
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = f"{temp_dir}/{file.filename}"

            with open(file_path, "wb") as binary_file:
                # Write bytes to file
                binary_file.write(file_contents)

            match file_type:
                case 'csv':
                    loader = CSVLoader(file_path)
                case 'excel':
                    loader = UnstructuredExcelLoader(file_path)         
                case 'docx':
                    loader=Docx2txtLoader(file_path)
                case 'md':
                    loader = UnstructuredMarkdownLoader(file_path)
                case 'pptx':
                    loader=UnstructuredPowerPointLoader(file_path)

            docs = loader.load()

            for i, _ in enumerate(docs):
                docs[i].metadata["filename"] = file.filename
                docs[i].metadata["source"] = urljoin(self.course_api, f"files/{file.id}")

        return docs
