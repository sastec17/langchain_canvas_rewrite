from canvasapi.exceptions import CanvasException
from canvas_langchain.base import BaseSectionLoader
from langchain.docstore.document import Document
from canvasapi.paginated_list import PaginatedList
from typing import List

from canvas_langchain.utils.common import format_data

class AssignmentLoader(BaseSectionLoader):
    def load(self) -> List[Document]:
        assignment_documents = []
        try:
            assignments = self.course.get_assignments()
            for doc in assignments:
                if f"Assignment:{doc.id}" not in self.indexed_items:
                    self.indexed_items.add(f"Assignment:{doc.id}")
                    assignment_documents.extend(self.load_assignment(doc))

        except CanvasException as error:
            print("Error loading assignments", error)

        return assignment_documents


    def load_assignment(self, assignment: PaginatedList) -> List[Document]:
        assignment_description = ""
        embed_urls = []
        if assignment.description:
            (assignment_description, embed_urls) = self.parse_html(assignment.description)
                                                                             
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
        return format_data(metadata=metadata, embed_urls=embed_urls)
