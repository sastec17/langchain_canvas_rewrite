from canvasapi.exceptions import CanvasException
from canvas_langchain.utils.embedded_media import parse_html_for_text_and_urls

def load_assignments(data):
    assignment_documents = []
    try:
        assignments = data['course'].get_assignments()
        for doc in assignments:
            if f"Assignment:{doc.id}" not in data['indexed_items']:
                data['indexed_items'].add(f"Assignment:{doc.id}")
                assignment_documents.append(load_assignment(data, doc))

    except CanvasException as error:
        print("Error loading assignments", error)

    return assignment_documents

def load_assignment(data, assignment):
    assignment_documents = []
    embed_urls = []
    if assignment.description:
        (assignment_description, embed_urls) = parse_html_for_text_and_urls(data.canvas, 
                                                                            data.course, 
                                                                            assignment_description)
    #TODO: clean this function 
    
    return