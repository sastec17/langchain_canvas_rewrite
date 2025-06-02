from canvasapi.exceptions import CanvasException
from canvas_langchain.utils.embedded_media import parse_html_for_text_and_urls
from canvas_langchain.utils.common import format_data

from langchain.docstore.document import Document
from typing import Dict, List
from urllib.parse import urljoin

# TODO: Set up mapping from allowed content types to functions?
# TODO: Determine if templated function(s) suffice for loading documents

def load_files(loader) -> List[Document]:
    """Loads and formats all files from Canvas course"""
    file_documents = []
    try:
        files = loader.course.get_files()

    except CanvasException as error:
        print("Canvas Exception loading files", error)
    return file_documents

