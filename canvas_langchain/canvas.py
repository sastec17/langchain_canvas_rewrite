import logging
from canvasapi import Canvas

from langchain.docstore.document import Document
from langchain.document_loaders.base import BaseLoader
from typing import List
from canvas_langchain.sections.syllabus import load_syllabus
from canvas_langchain.sections.assignments import load_assignments
from canvas_langchain.sections.announcements import load_announcements
from canvas_langchain.sections.pages import load_pages
from canvas_langchain.sections.files import load_files
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class CanvasLoader(BaseLoader):
    def __init__(self,
                 api_url: str,
                 api_key: str,
                 course_id: int, 
                 index_external_urls: bool=False):
        self.api_url = api_url
        self.api_key = api_key
        # TODO: DOES THIS NEED TO BE A MEMBER VARIABLE? 
        self.course_id = course_id
        self.index_external_urls = index_external_urls

        self.canvas = Canvas(api_url, api_key)
        self.course = self.canvas.get_course(self.course_id,
                                             include=['syllabus_body'])
        self.docs = []
        self.indexed_items = set()
        self.invalid_files = []
        self.progress = []

    def load(self) -> List[Document]:
        try:
            metadata = {
                "canvas": self.canvas,
                "course": self.course,
                "course_api": urljoin(self.api_url, f'/courses/{self.course.id}'),
                "indexed_items": self.indexed_items,
                "logger": logger
            }
            # load syllabus
            self.docs.extend(load_syllabus(metadata))

            # available course navigation tabs
            available_tabs = [tab.label for tab in self.course.get_tabs()]

            # TODO: INVESTIGATE IF MATCH+CASE OR IF/ELIF IS BETTER HERE
            load_actions = {
                'Announcements': lambda: load_announcements(metadata),
                'Assignments': lambda: load_assignments(metadata),
                'Files': lambda: load_files(metadata),
                'Pages': lambda: load_pages(metadata),
            }

            for tab_name, loader_func in load_actions.items():
                if tab_name in available_tabs:
                    self.docs.extend(loader_func())

        except Exception as error:
            print("Something went wrong", error)
        return self.docs

    def get_details(arg):
        return "No details here"
    