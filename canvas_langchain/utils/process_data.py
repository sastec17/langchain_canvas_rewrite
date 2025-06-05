from datetime import datetime, timezone
import logging
import settings
from typing import List, Tuple, Dict
from urllib.parse import urlparse

from langchain.docstore.document import Document
from canvas_langchain.sections.mivideo import MiVideoLoader

def process_data(metadata: Dict, embed_urls: List, mivideo_loader: MiVideoLoader) -> List[Document]:
    """Process metadata and embed_urls on a single 'page'"""
    document_arr = []    
    # Format metadata
    if metadata['content']:
        document_arr.append(Document(
            page_content=metadata['content'],
            metadata=metadata['data']
        ))
    # Load content from embed urls
    document_arr.extend(_load_embed_urls(metadata=metadata, embed_urls=embed_urls, mivideo_loader=mivideo_loader))
    return document_arr


def _load_embed_urls(metadata: Dict, 
                     embed_urls: List, 
                     mivideo_loader: MiVideoLoader) -> List[Document]:
    """Load MiVideo content from embed urls"""
    # needs metadata, urls, mivideoloader
    docs = []
    for url in embed_urls:
        mivideo_loader.logger.debug("Loading embed url %s", url)
        # extract media_id from each url + load captions
        if (mivideo_media_id := _get_media_id(url)):
            docs.extend(mivideo_loader.load(mivideo_id=mivideo_media_id,
                                            logger=mivideo_loader.logger))
        
    for doc in docs:
        doc.metadata.update({'filename': str(metadata['data']['filename']), 
                                'course_context': str(metadata['data']['source'])})
    return docs


def _get_media_id(url: str, logger: logging) -> str | None:
    """Extracts unique media id from each URL to load mivideo"""
    parsed=urlparse(url)
    # TODO: AVOID HARDCODING THIS - How best to load this? 
    if parsed.netloc == (settings.MIVIDEO_KAF_HOSTNAME or 'aakaf.mivideo.it.umich.edu'): 
        path_parts = parsed.path.split('/')
        try:
            return path_parts[path_parts.index('entryid')+1]
        except ValueError:
            logger.info(f"Embed URL for {url} is not MiVideo")
    return None


# TODO: determine if returned time should be formatted differently?
def get_module_metadata(unlock_time: str) -> Tuple[bool, str]:
    """Returns whether module is locked AND when it's going to be unlocked"""
    locked=False
    formatted_datetime=""
    if unlock_time:
        # Convert to a timezone-aware datetime object
        formatted_datetime = datetime.strptime(unlock_time, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        # Get the current time in UTC
        current_time = datetime.now(timezone.utc)
        # Determine if locked
        locked = current_time < formatted_datetime

    return locked, formatted_datetime
