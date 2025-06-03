from langchain.docstore.document import Document
from typing import List
from urllib.parse import urlparse
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
