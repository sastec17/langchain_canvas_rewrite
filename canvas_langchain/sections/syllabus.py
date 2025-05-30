from canvas_langchain.utils.embedded_media import parse_html_for_text_and_urls
from canvas_langchain.utils.common import format_data
from langchain.docstore.document import Document
from urllib.parse import urljoin

def load_syllabus(data):
    if data['course'].syllabus_body: 
        try:
            (syllabus_text, embed_urls) = parse_html_for_text_and_urls(canvas=data['canvas'],
                                                                    course=data['course'],
                                                                    html=data['course'].syllabus_body)
            syllabus_url = urljoin(data['course_api'], '/assignments/syllabus')

            metadata={"content": syllabus_text,
                      "data": {"filename": "Course Syllabus",
                               "source": syllabus_url,
                               "kind": "syllabus"}
                        }
            formatted_data = format_data(metadata=metadata, embed_urls=embed_urls)

        except AttributeError as error:
            print('ATTRIBUTE ERR', error)
    return formatted_data
