from datetime import date
from typing import List

from canvas_langchain.base import BaseSectionLoader
from canvasapi.exceptions import CanvasException
from canvas_langchain.utils.common import format_data
from langchain.docstore.document import Document


class AnnouncementLoader(BaseSectionLoader):
    def load(self) -> List[Document]:
        """Load all announcements for a Canvas course"""
        self.logger.info("Loading announcements...")
        announcement_documents = embed_urls = []
        try:
            announcements = self.canvas.get_announcements(context_codes=[self.course],
                                                            start_date="2016-01-01",
                                                            end_date=date.today().isoformat())

            for announcement in announcements:
                announcement_text, embed_urls = self.parse_html(html=announcement.message)
                
                metadata={"content": announcement_text,
                        "data": {"filename": announcement.title,
                                "source": announcement.html_url,
                                "kind": "announcement",
                                "id": announcement.id}
                        }
                
                formatted_data = format_data(metadata=metadata, embed_urls=embed_urls)
                                                                                                                    
                announcement_documents.extend(formatted_data)

        except CanvasException as error:
            self.logger.error("Canvas exception loading announcements %s", error)

        return announcement_documents
