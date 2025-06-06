from typing import List
from urllib.parse import urljoin

from canvas_langchain.base import BaseSectionLoader
from langchain.docstore.document import Document

class SyllabusLoader(BaseSectionLoader):
    def load(self) -> List[Document]:
        self.logger.logStatement(message='Loading syllabus...\n', level="INFO")
        if self.course.syllabus_body:
            try:
                syllabus_text, embed_urls = self.parse_html(self.course.syllabus_body)
                syllabus_url = urljoin("", '/assignments/syllabus')

                metadata={"content": syllabus_text,
                        "data": {"filename": "Course Syllabus",
                                "source": syllabus_url,
                                "kind": "syllabus"}
                            }
                return self.process_data(metadata=metadata, embed_urls=embed_urls)

            except AttributeError as err:
                self.logger.logStatement(message=f"Attribute error loading syllabus: {err}", level="WARNING")

        return []
