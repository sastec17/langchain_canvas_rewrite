from langchain.docstore.document import Document
from typing import List, Tuple
from urllib.parse import urlparse
import datetime
import pytz
# from canvas_langchain.sections.mivideo import load_mivideo

def format_data(metadata, embed_urls) -> List[Document]:
    """Process metadata and embed_urls on a single 'page'"""
    document_arr = []    
    # Format metadata
    if metadata['content']:
        document_arr.append(Document(
            page_content=metadata['content'],
            metadata=metadata['data']
        ))

    # Load content from embed urls
    # TODO: uncomment this 
    #document_arr.append(load_embed_urls(metadata=metadata, embed_urls=embed_urls))
    return document_arr


def load_embed_urls(metadata, embed_urls):
    """Load MiVideo content from embed urls"""
    docs = []
    for url in embed_urls:
        # extract media_id from each url + load captions
        if (mivideo_media_id := _get_media_id(url)):
            print('sup')
            #docs.append(load_mivideo(media_id = mivideo_media_id))
        
    for doc in docs:
        doc.metadata.update({'filename': metadata['name'], 'course_context': metadata['source']})
    return docs


def _get_media_id(url: str) -> str | None:
    """Extracts unique media id from each URL to load mivideo"""
    parsed=urlparse(url)
    # TODO: AVOID HARDCODING THIS - How best to load this? 
    if parsed.netloc == 'aakaf.mivideo.it.umich.edu':
        path_parts = parsed.path.split('/')
        try:
            return path_parts[path_parts.index('entryid')+1]
        except ValueError:
            print('EMBED URL NOT FOR MIVIDEO')
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
