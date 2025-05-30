from langchain.docstore.document import Document
from typing import List

def format_data(metadata, embed_urls) -> List[Document]:
    """Formats document with metadata and associated embed_urls"""
    if metadata['content']:
        document = Document(
            page_content=metadata['content'],
            metadata=metadata['data']
        )
    else:
        return []

    # TODrO: Add embed_urls logic
    # CALL load_media_embeds here
    return [document]