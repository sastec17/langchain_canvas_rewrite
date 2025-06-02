from canvasapi.exceptions import CanvasException
from canvas_langchain.utils.embedded_media import parse_html_for_text_and_urls
from langchain.docstore.document import Document
from canvasapi.paginated_list import PaginatedList
from typing import Dict, List

from canvas_langchain.utils.common import format_data

def load_assignments(loader) -> List[Document]:
    assignment_documents = []
    try:
        assignments = loader.course.get_assignments()
        for doc in assignments:
            if f"Assignment:{doc.id}" not in loader.indexed_items:
                loader.indexed_items.add(f"Assignment:{doc.id}")
                assignment_documents.extend(load_assignment(loader, doc))

    except CanvasException as error:
        print("Error loading assignments", error)

    return assignment_documents


def load_assignment(loader, assignment: PaginatedList) -> List[Document]:
    assignment_description = ""
    embed_urls = []
    if assignment.description:
        (assignment_description, embed_urls) = parse_html_for_text_and_urls(loader.canvas, 
                                                                            loader.course,
                                                                            assignment.description) 
    # TODO: Shorten assignment content - Is "Assignment" needed before every tag?                                                                     assignment.description)
    assignment_content = (
        f"Assignment Name: {assignment.name}\n"
        f"Assignment Due Date: {assignment.due_at}\n"
        f"Assignment Points Possible: {assignment.points_possible}\n"
        f"Assignment Description: {assignment_description}\n"
    )

    metadata={"content":assignment_content,
              "data": {"filename": assignment.name,
                       "source": assignment.html_url,
                       "kind": "assignment",
                       "id": assignment.id}
                }
    formatted_data = format_data(metadata=metadata, embed_urls=embed_urls)
    
    return formatted_data
