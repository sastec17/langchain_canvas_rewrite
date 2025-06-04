import logging
from typing import List
from canvasapi import Canvas
from urllib.parse import urljoin
from langchain.document_loaders.base import BaseLoader
from langchain.docstore.document import Document
from canvasapi.exceptions import CanvasException
from langchain_community.document_loaders import UnstructuredURLLoader

from canvas_langchain.utils.common import get_module_metadata
from canvas_langchain.sections.announcements import AnnouncementLoader
from canvas_langchain.sections.assignments import AssignmentLoader
from canvas_langchain.sections.files import FileLoader
from canvas_langchain.sections.mivideo import MiVideoLoader
from canvas_langchain.sections.pages import PageLoader
from canvas_langchain.sections.syllabus import SyllabusLoader
from canvas_langchain.base import BaseSectionLoaderVars

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
# Quiet noisy libraries
logging.getLogger("canvasapi").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("LangChainKaltura").setLevel(logging.WARNING)

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
        self.mivideo_loader = MiVideoLoader(self.canvas, self.course, self.indexed_items, logger)

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
        """Loads all available content from Canvas course"""
        logger.info("Starting document loading process. \n")
        try:
            # load syllabus
            self.docs.extend(self.syllabus_loader.load())

            # get available course navigation tabs
            available_tabs = [tab.label for tab in self.course.get_tabs()]

            for tab_name in available_tabs:
                match tab_name:
                    case 'Announcements':
                        self.docs.extend(self.announcement_loader.load())
                    case 'Assignments':
                        self.docs.extend(self.assignment_loader.load())
                    case 'Media Gallery':
                        self.docs.extend(self.mivideo_loader.load(mivideo_id=None))
                    case 'Modules':
                        self.docs.extend(self.load_modules())
                    case 'Pages': 
                        self.docs.extend(self.page_loader.load_pages())
                    case 'Files':
                        self.docs.extend(self.file_loader.load_files())

        except Exception as error:
            logging.error("Error loading Canvas materials %s", error)
        logger.info("Canvas course processing finished.")
        return self.docs
    

    def load_modules(self) -> List[Document]:
        """Loads content from all unlocked modules in course"""
        logger.info('Loading modules...\n')
        module_documents = []
        try:
            modules = self.course.get_modules()
            module_documents.extend(self.load_module(module) for module in modules)

        except CanvasException as ex:
            logger.error("Canvas exception loading modules %s", ex)

        return module_documents


    def load_module(self, module) -> List[Document]:
        """Loads all content in module by type"""
        locked, formatted_datetime = get_module_metadata(module.unlock_at)
        module_items = module.get_module_items(include=["content_details"])
        module_docs = []
        #TODO: consider try/ except within for loop, outside of conditionals and extra logging
        for item in module_items:
            try:
                # page
                if item.type == "Page" and not locked:
                    logger.debug("Loading pages %s from module", item.page_url)
                    page = self.course.get_page(item.page_url)
                    module_docs.extend(self.page_loader.load_page(page))

                # assignment metadata can be gathered, even if module is locked
                elif item.type == "Assignment":
                    logger.debug("Loading assignments %s from module", item.content_id)
                    assignment = self.course.get_assignment(item.content_id)
                    description=None
                    if locked and formatted_datetime:
                        description=f"Assignment is part of module {module.name}, which is locked until {formatted_datetime}"
                    #self.assignment_loader.load_assignment(assignment, description)
                    module_docs.extend(self.assignment_loader.load_assignment(assignment, description))

                #TODO
                # file - Need Reource DNE exception here?
                elif item.type=="File":
                    logger.debug("Loading file %s from module", item.content_id)
                    file = self.course.get_file(item.content_id)
                    module_docs.extend(self.file_loader.load_file(file))

                # TODO: TEST THIS - case where externalUrls wouldn't be true? 
                # Clean up conditional - Feels a smidge unreadable
                elif item.type=="ExternalUrl" and self.index_external_urls and \
                    not locked and f"ExtUrl:{item.external_url}" not in self.indexed_items:
                    logger.debug("Loading external URL %s from module", item.external_url)
                    # load URL
                    url_loader = UnstructuredURLLoader(urls = [item.external_url])
                    module_docs.extend(url_loader.load())
                    self.indexed_items.append(f"ExtUrl:{item.external_url}")

            except CanvasException as ex:
                logger.error("Unable to load %s item in module %s. Error: %s", item, module.name, ex)

        return module_docs


    def get_details(arg):
        return "No details here"
