from canvas_langchain.utils.embedded_media import parse_html_for_text_and_urls

class BaseSectionLoader:
    def __init__(self, canvas, course):
        self.canvas = canvas
        self.course = course
        print("INITIALIZING HERE")
        return
    
    def parse_html(self, html):
        return parse_html_for_text_and_urls(self.canvas, 
                                            self.course, 
                                            html)