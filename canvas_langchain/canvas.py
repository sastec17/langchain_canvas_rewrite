import logging
from typing import List
from canvasapi import Canvas
from urllib.parse import urljoin
from langchain.document_loaders.base import BaseLoader
from langchain.docstore.document import Document

from canvas_langchain.sections.announcements import AnnouncementLoader
from canvas_langchain.sections.assignments import AssignmentLoader
from canvas_langchain.sections.files import FileLoader
from canvas_langchain.sections.mivideo import MiVideoLoader
from canvas_langchain.sections.pages import PageLoader
from canvas_langchain.sections.syllabus import SyllabusLoader
from canvas_langchain.base import BaseSectionLoaderVars

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class CanvasLoader(BaseLoader):
    def __init__(self,
                 api_url: str,
                 api_key: str,
                 course_id: int, 
                 index_external_urls: bool=False):
        self.index_external_urls = index_external_urls

        self.canvas = Canvas(api_url, api_key)
        self.course = self.canvas.get_course(course_id,
                                             include=['syllabus_body'])
        self.course_api = urljoin(api_url, f'/courses/{self.course.id}/')

        self.docs = []
        self.indexed_items = set()
        self.invalid_files = []
        self.progress = []

        # content loaders
        self.mivideo_loader = MiVideoLoader(self.canvas, self.course, self.indexed_items)

        self.baseSectionVars = BaseSectionLoaderVars(self.canvas, 
                                                     self.course, 
                                                     self.indexed_items, 
                                                     self.mivideo_loader,
                                                     logger)

        self.file_loader = FileLoader(self.baseSectionVars, self.course_api, self.invalid_files)
        self.syllabus_loader = SyllabusLoader(self.baseSectionVars)
        self.announcement_loader = AnnouncementLoader(self.baseSectionVars)
        self.assignment_loader = AssignmentLoader(self.baseSectionVars)
        self.page_loader = PageLoader(self.baseSectionVars, self.course_api)

    def load(self) -> List[Document]:
        logger.info("Starting document loading process")
        try:
            # load syllabus
            self.docs.extend(self.syllabus_loader.load())

            # get available course navigation tabs
            available_tabs = [tab.label for tab in self.course.get_tabs()]

            for tab_name in available_tabs:
                match tab_name:
                    # case 'Announcements':
                    #     self.announcement_loader.load()
                    # case 'Assignments':
                    #     self.assignment_loader.load()
                    case 'Media Gallery':
                        self.mivideo_loader.load()
                    # case 'Pages': 
                    #     self.page_loader.load_pages()
                    # case 'Files':
                    #     self.file_loader.load_files()

        except Exception as error:
            logging.error("Error loading Canvas materials", error)
        return self.docs

    def get_details(arg):
        return "No details here"
    