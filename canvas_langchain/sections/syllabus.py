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


# def load_syllabus(loader) -> List[Document]:
#     if loader.course.syllabus_body: 
#         try:
#             (syllabus_text, embed_urls) = parse_html_for_text_and_urls(canvas=loader.canvas,
#                                                                     course=loader.course,
#                                                                     html=loader.course.syllabus_body)
#             syllabus_url = urljoin(loader.course_api, '/assignments/syllabus')

#             metadata={"content": syllabus_text,
#                       "data": {"filename": "Course Syllabus",
#                                "source": syllabus_url,
#                                "kind": "syllabus"}
#                         }
#             formatted_data = format_data(metadata=metadata, embed_urls=embed_urls)

#         except AttributeError as error:
#             print('ATTRIBUTE ERR', error)
#     return formatted_data
