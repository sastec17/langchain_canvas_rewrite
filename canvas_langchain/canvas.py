from canvasapi import Canvas

from langchain.docstore.document import Document
from langchain.document_loaders.base import BaseLoader
from typing import List
from sections.syllabus import load_syllabus
from urllib.parse import urljoin


class CanvasLoader(BaseLoader):
    def __init__(self,
                 api_url: str,
                 api_key: str,
                 course_id: int, 
                 index_external_urls: bool):
        self.api_url = api_url
        self.api_key = api_key
        # TODO: DOES THIS NEED TO BE A MEMBER VARIABLE? 
        self.course_id = course_id
        self.index_external_urls = index_external_urls

        self.canvas = Canvas(api_url, api_key)
        self.course = self.canvas.get_course(self.course_id,
                                             include=['syllabus_body'])
        self.docs = []
        return
    
    def load(self) -> List[Document]:
        try:
            metadata = {
                "canvas": self.canvas,
                "course": self.course,
                "course_api": urljoin(self.api_url, f'/courses/{self.course.id}')
            }
            # load syllabus
            self.docs.extend(load_syllabus(metadata))
        except:
            print("Something went wrong")
        return self.docs