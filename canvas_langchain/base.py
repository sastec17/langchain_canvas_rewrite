import logging
from typing import List, Dict
from urllib.parse import urlparse
import settings

from canvasapi import Canvas
from canvasapi.course import Course
from dataclasses import dataclass
from langchain.docstore.document import Document
from canvas_langchain.utils.embedded_media import parse_html_for_text_and_urls


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
        return parse_html_for_text_and_urls(self.canvas, 
                                            self.course, 
                                            html)
    
    def process_data(self, metadata: Dict, embed_urls: List) -> List[Document]:
        """Process metadata and embed_urls on a single 'page'"""
        document_arr = []    
        # Format metadata
        if metadata['content']:
            document_arr.append(Document(
                page_content=metadata['content'],
                metadata=metadata['data']
            ))
        # Load content from embed urls
        document_arr.extend(self._load_embed_urls(metadata=metadata, embed_urls=embed_urls))
        return document_arr


    def _load_embed_urls(self, metadata: Dict, embed_urls: List) -> List[Document]:
        """Load MiVideo content from embed urls"""
        docs = []
        for url in embed_urls:
            self.logger.debug("Loading embed url %s", url)
            # extract media_id from each url + load captions
            if (mivideo_media_id := self._get_media_id(url)):
                docs.extend(self.mivideo_loader.load(mivideo_id=mivideo_media_id))
            
        for doc in docs:
            doc.metadata.update({'filename': str(metadata['data']['filename']), 
                                 'course_context': str(metadata['data']['source'])})
        return docs


    # TODO: COULD PUT INTO HELPER FILE IF NEEDED - GENERAL GETTER
    def _get_media_id(self, url: str) -> str | None:
        """Extracts unique media id from each URL to load mivideo"""
        parsed=urlparse(url)
        # TODO: AVOID HARDCODING THIS - How best to load this? 
        if parsed.netloc == (settings.MIVIDEO_KAF_HOSTNAME or 'aakaf.mivideo.it.umich.edu'): 
            path_parts = parsed.path.split('/')
            try:
                return path_parts[path_parts.index('entryid')+1]
            except ValueError:
                self.logger.info(f"Embed URL for {url} is not MiVideo")
        return None
