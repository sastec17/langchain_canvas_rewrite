import logging
from canvasapi import Canvas

from langchain.docstore.document import Document
from langchain.document_loaders.base import BaseLoader
from typing import List
from canvas_langchain.sections.syllabus import SyllabusLoader
from canvas_langchain.sections.assignments import AssignmentLoader
from canvas_langchain.sections.announcements import AnnouncementLoader
from canvas_langchain.sections.pages import PageLoader
# from canvas_langchain.sections.files import load_files
from urllib.parse import urljoin

logging.basicConfig(level=logging.DEBUG)
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

        self.syllabus_loader = SyllabusLoader(self.canvas, self.course)
        self.announcement_loader = AnnouncementLoader(self.canvas, self.course)
        self.page_loader = PageLoader(self.canvas, self.course, self.indexed_items, self.api_url)

    def load(self) -> List[Document]:
        logger.info("Starting document loading process")
        try:
            # load syllabus
            self.docs.extend(self.syllabus_loader.load())

            # get available course navigation tabs
            available_tabs = [tab.label for tab in self.course.get_tabs()]

            # TODO: INVESTIGATE IF MATCH+CASE OR IF/ELIF IS BETTER HERE
            load_actions = {
                'Announcements': lambda: self.announcement_loader.load(),
                # 'Assignments': load_assignments,
               # 'Files': load_files,
                'Pages': lambda: self.page_loader.load_all(),
            }
            #self.announcement_loader.load()
            for tab_name, loader_func in load_actions.items():
                if tab_name in available_tabs:
                    self.docs.extend(loader_func())

        except Exception as error:
            logging.error("Error loading Canvas materials", error)
        return self.docs

    def get_details(arg):
        return "No details here"
    