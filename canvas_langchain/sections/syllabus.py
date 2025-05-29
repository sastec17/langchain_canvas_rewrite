from canvas_langchain.utils.embedded_media import parse_html_for_text_and_urls
from langchain.docstore.document import Document
from urllib.parse import urljoin

def load_syllabus(data):
    syllabus_docs = []
    if data['course'].syllabus_body: 
        try:
            (syllabus_text, embed_urls) = parse_html_for_text_and_urls(canvas=data['canvas'],
                                                                    course=data['course'],
                                                                    html=data['course'].syllabus_body)
            syllabus_url = urljoin(data['course_api'], '/assignments/syllabus')
            if (syllabus_text):
                syllabus_doc = Document(page_content=syllabus_text,
                                        metadata={"filename": "Course Syllabus",
                                                  "source": syllabus_url,
                                                  "kind": "syllabus"})

                syllabus_docs.append(syllabus_doc)

            #TODO: APPEND EMBED_URLS TO LOAD & ADD YOUTUBE SUPPORT
        except AttributeError:
            print('ATTRIBUTE ERR')
    return syllabus_docs
