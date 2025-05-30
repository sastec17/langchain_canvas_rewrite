from canvasapi.exceptions import CanvasException
from canvas_langchain.utils.embedded_media import parse_html_for_text_and_urls
from langchain.docstore.document import Document
from canvasapi.paginated_list import PaginatedList
from typing import Dict, List

from canvas_langchain.utils.common import format_data

def load_assignments(data: Dict[str, any]) -> List[Document]:
    assignment_documents = []
    try:
        assignments = data['course'].get_assignments()
        for doc in assignments:
            if f"Assignment:{doc.id}" not in data['indexed_items']:
                data['indexed_items'].add(f"Assignment:{doc.id}")
                assignment_documents.extend(load_assignment(data, doc))

    except CanvasException as error:
        print("Error loading assignments", error)

    return assignment_documents


def load_assignment(data: Dict[str, any], assignment: PaginatedList) -> List[Document]:
    assignment_description = ""
    embed_urls = []
    if assignment.description:
        (assignment_description, embed_urls) = parse_html_for_text_and_urls(data["canvas"], 
                                                                   data["course"],
                                                                   assignment.description) 
    # TODO: Shorten assignment content - Is "Assignment" needed before every tag?                                                                     assignment.description)
    assignment_content = (
        f"Assignment Name: {assignment.name}\n"
        f"Assignment Due Date: {assignment.due_at}\n"
        f"Assignment Points Possible: {assignment.points_possible}\n"
        f"Assignment Description: {assignment_description}\n"
    )

    formatted_data = format_data(doc_content=assignment_content, 
                                 doc=assignment, 
                                 doc_type='assignment', 
                                 embed_urls=embed_urls)
    return formatted_data
