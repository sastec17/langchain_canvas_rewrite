import logging
from typing import List, Dict
from dataclasses import dataclass

from canvasapi import Canvas
from canvasapi.course import Course
from langchain.docstore.document import Document
from canvas_langchain.utils.embedded_media import parse_html_for_text_and_urls
from canvas_langchain.utils.process_data import process_data

@dataclass
class BaseSectionLoaderVars:
    canvas : Canvas
    course: Course
    indexed_items: set
    mivideo_loader: int
    logger: logging


class BaseSectionLoader:
    """Contains member variables and functions required across all loading classes"""
    def __init__(self, baseSectionVars: BaseSectionLoaderVars):
        self.canvas = baseSectionVars.canvas
        self.course = baseSectionVars.course
        self.indexed_items = baseSectionVars.indexed_items
        self.mivideo_loader = baseSectionVars.mivideo_loader
        self.logger = baseSectionVars.logger


    def parse_html(self, html):
        """Extracts text and a list of embedded urls from HTML content"""
        return parse_html_for_text_and_urls(canvas=self.canvas, 
                                            course=self.course, 
                                            html=html)
    
    def process_data(self, metadata: Dict, embed_urls: List) -> List[Document]:
        """Process metadata and embed_urls on a single 'page'"""
        return process_data(metadata=metadata, 
                            embed_urls=embed_urls,
                            mivideo_loader=self.mivideo_loader)
