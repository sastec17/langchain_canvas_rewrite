from typing import List

from canvas_langchain.base import BaseSectionLoader
from canvas_langchain.utils.common import format_data
from langchain.docstore.document import Document
from urllib.parse import urljoin

class SyllabusLoader(BaseSectionLoader):
    def load(self) -> List[Document]:
        if self.course.syllabus_body:
            try:
                syllabus_text, embed_urls = self.parse_html(self.course.syllabus_body)
                syllabus_url = urljoin("", '/assignments/syllabus')

                metadata={"content": syllabus_text,
                        "data": {"filename": "Course Syllabus",
                                "source": syllabus_url,
                                "kind": "syllabus"}
                            }
                return format_data(metadata=metadata, embed_urls=embed_urls)

            except AttributeError as err:
                print("ERROR WITH LOADING SYLLABUS", err)
        return []
