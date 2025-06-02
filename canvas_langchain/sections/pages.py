from canvas_langchain.base import BaseSectionLoader

from canvasapi.exceptions import CanvasException
from canvas_langchain.utils.common import format_data

from langchain.docstore.document import Document
from typing import List
from urllib.parse import urljoin

class PageLoader(BaseSectionLoader):
    def __init__(self, canvas, course, indexed_items, course_api):
        super().__init__(canvas, course)
        self.indexed_items = indexed_items
        self.course_api = course_api

    def load_all(self) -> List[Document]:
        page_documents = []

        try:
            pages = self.course.get_pages(published=True,
                                            include=['body'])
            for page in pages:
                if f"Page:{page.page_id}" not in self.indexed_items:
                    self.indexed_items.add(f"Page:{page.page_id}")
                    page_documents.extend(self.load_page(page))

        except CanvasException as error:
            print("Canvas Exception when loading pages", error)
        
        return page_documents


    def load_page(self, page) -> List[Document]:
        """Loads and formats a single page and its embedded URL(s) content """
        page_docs = []
        if not page.locked_for_user and page.body:
            page_body, embed_urls = self.parse_html(html=page.body)
           
            page_url = urljoin(self.course_api, f'/pages/{page.url}')
            metadata={"content": page_body,
                    "data": {"filename": page.title,
                                "source": page_url,
                                "kind": "page",
                                "id": page.page_id}
                    }
            page_docs = format_data(metadata=metadata, embed_urls=embed_urls)                                                      
        return page_docs
