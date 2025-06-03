import os
from dataclasses import dataclass
import logging
from langchain.docstore.document import Document
from typing import List
from canvas_langchain.utils.embedded_media import parse_html_for_text_and_urls
from urllib.parse import urlparse
from canvasapi import Canvas
from canvasapi.course import Course

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

        return
    
    def parse_html(self, html):
        """Extracts text and a list of embedded urls from HTML content"""
        return parse_html_for_text_and_urls(self.canvas, 
                                            self.course, 
                                            html)
    
    def format_data(self, metadata, embed_urls) -> List[Document]:
        """Process metadata and embed_urls on a single 'page'"""
        document_arr = []    
        # Format metadata
        if metadata['content']:
            document_arr.append(Document(
                page_content=metadata['content'],
                metadata=metadata['data']
            ))
        # Load content from embed urls
        document_arr.append(self._load_embed_urls(metadata=metadata, embed_urls=embed_urls))
        return document_arr


    def _load_embed_urls(self, metadata, embed_urls):
        """Load MiVideo content from embed urls"""
        docs = []
        for url in embed_urls:
            # extract media_id from each url + load captions
            if (mivideo_media_id := self._get_media_id(url)):
                docs.append(self.load_mivideo(media_id = mivideo_media_id))
            
        for doc in docs:
            doc.metadata.update({'filename': metadata['name'], 'course_context': metadata['source']})
        return docs


    # TODO: COULD PUT INTO HELPER FILE IF NEEDED - GENERAL GETTER
    def _get_media_id(self, url: str) -> str | None:
        """Extracts unique media id from each URL to load mivideo"""
        parsed=urlparse(url)
        # TODO: AVOID HARDCODING THIS - How best to load this? 
        if parsed.netloc == os.getenv('MIVIDEO_KAF_HOSTNAME',
                                              'aakaf.mivideo.it.umich.edu'):
            path_parts = parsed.path.split('/')
            try:
                return path_parts[path_parts.index('entryid')+1]
            except ValueError:
                self.logger.info(f"Embed URL for {url} is not MiVideo")
        return None
