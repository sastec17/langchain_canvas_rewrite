from langchain.docstore.document import Document
from typing import List

def format_data(doc_content, doc, doc_type, embed_urls) -> List[Document]:
    """Formats document with metadata and associated embed_urls"""
    document = Document(
        page_content=doc_content,
        metadata={"filename": doc.name,
                  "source": doc.html_url,
                  "kind": doc_type,
                  "id": doc.id
        }
    )
    

    # TODO: Add embed_urls logic
    # CALL load_media_embeds here
    return [document]