import datetime
import logging
import pytz
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


# TODO: Cleanup
def get_module_metadata(unlock_time: str) -> Tuple[bool, str]:
    """Returns whether module is locked AND when it's going to be unlocked"""
    locked=False
    formatted_datetime=""
    # Takes in module.unlock_at
    # Returns if locked and the formatted module unlock time
    if unlock_time:
        unlock_at_datetime = datetime.striptime(unlock_time, '%Y-%m-%dT%H:%M:%SZ')
        unlock_at_datetime = unlock_at_datetime.replace(tzinfo=pytz.UTC)
        epoch_time = int(unlock_at_datetime.timestamp())
        current_epoch_time = int(datetime.now().timestamp())
        # Get current time 
        # Figure out timezone we are currently in - Ensure datetime passed in is in same timezone

        # Why are we hardcoding the timezone??? - Find a way to extract timezone 

        # Use to specify when the timezone will end
        if current_epoch_time < epoch_time:
            locked = True
            # NEED FORMATTED DATETIME FOR LOAD_ASSIGNMENT - format here
            ny_timezone = pytz.timezone('America/New_York')
            ny_datetime = unlock_at_datetime.astimezone(ny_timezone)
            formatted_datetime = ny_datetime.strftime("%b %d, %Y at %I%p %Z").replace("PM", "pm").replace("AM", 'am')

    return locked, formatted_datetime
