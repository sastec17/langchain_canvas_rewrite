from canvas_langchain.base import BaseSectionLoader
from canvasapi.exceptions import CanvasException, ResourceDoesNotExist
from canvas_langchain.utils.file_load import (
load_html_file
)

from langchain.docstore.document import Document
from typing import List

# TODO: Set up mapping from allowed content types to functions?
# TODO: Determine if templated function(s) suffice for loading documents

class FileLoader(BaseSectionLoader):
    def __init__(self, canvas, course, indexed_items):
        super().__init__(canvas, course)
        self.indexed_items = indexed_items

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
        try:
            # map from content type to loading function
            content = {
                # "text/plain": _load_text_file,
                # "text/html": _load_html_file,
            }
            content_type = getattr(file, "content-type")
            # execute mapped function
            if content_type in content:
                return content[content_type](file)
            else:
                print("File is not a valid content type")

        except ResourceDoesNotExist:
            print('Huzzah hit this first')
        return []

