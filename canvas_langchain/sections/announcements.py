from datetime import date
from canvasapi.exceptions import CanvasException
from canvas_langchain.utils.embedded_media import parse_html_for_text_and_urls
from canvas_langchain.utils.common import format_data

from langchain.docstore.document import Document
from typing import List

def load_announcements(loader) -> List[Document]:
    announcement_documents = embed_urls = []
    try:
        announcements = loader.canvas.get_announcements(context_codes=[loader.course],
                                                         start_date="2016-01-01",
                                                         end_date=date.today().isoformat())

        for announcement in announcements:
            (announcement_text, embed_urls) = parse_html_for_text_and_urls(loader.canvas,
                                                                           loader.course,
                                                                           announcement.message)
            metadata={"content": announcement_text,
                      "data": {"filename": announcement.title,
                              "source": announcement.html_url,
                              "kind": "announcement",
                              "id": announcement.id}
                      }
            
            formatted_data = format_data(metadata=metadata, embed_urls=embed_urls)
                                                                                                                   
            announcement_documents.extend(formatted_data)

    except CanvasException as error: 
        print('ERROR LOADING ANNOUNCEMENTS', error)

    return announcement_documents
