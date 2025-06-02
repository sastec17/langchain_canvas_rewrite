from canvasapi.exceptions import CanvasException
from canvas_langchain.utils.embedded_media import parse_html_for_text_and_urls
from canvas_langchain.utils.common import format_data

from langchain.docstore.document import Document
from typing import List
from urllib.parse import urljoin

def load_pages(loader) -> List[Document]:
    """Loads all pages in canvas course"""
    page_documents = []

    try:
        pages = loader.course.get_pages(published=True,
                                         include=['body'])
        for page in pages:
            if f"Page:{page.page_id}" not in loader.indexed_items:
                loader.indexed_items.add(f"Page:{page.page_id}")
                page_documents.extend(load_page(loader, page))

    except CanvasException as error:
        print("Canvas Exception when loading pages", error)
    
    return page_documents


def load_page(loader, page) -> List[Document]:
    """Loads and formats a single page and its embedded URL(s) content """
    page_docs = []
    if not page.locked_for_user and page.body:
        (page_body, embed_urls) = parse_html_for_text_and_urls(canvas=loader.canvas,
                                                               course=loader.course,
                                                               html=page.body)
        page_url = urljoin(loader.course_api, f'/pages/{page.url}')
        metadata={"content": page_body,
                 "data": {"filename": page.title,
                            "source": page_url,
                            "kind": "page",
                            "id": page.page_id}
                }
        page_docs = format_data(metadata=metadata, embed_urls=embed_urls)                                                      

    return page_docs
