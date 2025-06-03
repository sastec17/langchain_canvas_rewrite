import os
from typing import List

from langchain.docstore.document import Document
from LangChainKaltura import KalturaCaptionLoader
from LangChainKaltura.MiVideoAPI import MiVideoAPI

class MiVideoLoader():
    def __init__(self, canvas, course, indexed_items, logger):
        self.canvas = canvas
        self.course = course
        self.indexed_items = indexed_items
        self.logger = logger
        self.caption_loader = None
        self.mivideo_api = MiVideoAPI(host=os.getenv('MIVIDEO_API_HOST'),
                                      authId=os.getenv('MIVIDEO_API_AUTH_ID'),
                                      authSecret=os.getenv('MIVIDEO_API_AUTH_SECRET'))


    def load(self, mivideo_id: str | None) -> List[Document]:
        """Load MiVideo media captions"""
        mivideo_docuements = []
        self.logger.debug("Loading MiVideo captions for %s", mivideo_id)
        try:
            if not self.caption_loader:
                self.caption_loader = self._get_caption_loader()
            
            # Load entire media gallery
            if mivideo_id is None:
                mivideo_docuements = self.caption_loader.load()

            # Load single media post - likely embedded
            elif f"MiVideo:{mivideo_id}" not in self.indexed_items:
                mivideo_docuements = self.caption_loader.fetchMediaCaption({
                    'id': mivideo_id,
                    'name': 'unidentified embedded media'
                })

            course_url_template = os.getenv('CANVAS_COURSE_URL_TEMPLATE')
            for doc in mivideo_docuements:
                # add formatted course source url for this video
                if course_url_template:
                    doc.metadata['course_context'] = course_url_template.format(courseId=self.course.id)
                self.indexed_items.add("MiVideo:"+doc.metadata['media_id'])

        except Exception as ex:
            self.logger.error("Error loading MiVideo content %s", ex)

        return mivideo_docuements
    
    def _get_caption_loader(self) -> KalturaCaptionLoader:
        # TODO: determine if custom languages needed
        try: 
            languages = KalturaCaptionLoader.LANGUAGES_DEFAULT
            # TODO: REVISE SOME OF THESE VALUES
            caption_loader = KalturaCaptionLoader(
                apiClient=self.mivideo_api,
                courseId=str(int(self.course.id)),
                userId=os.getenv('CANVAS_USER_ID_OVERRIDE_DEV_ONLY',
                                 self.canvas.get_current_user().id),
                languages=languages,
                urlTemplate=os.getenv('MIVIDEO_SOURCE_URL_TEMPLATE'),
                chunkSeconds=int(KalturaCaptionLoader.CHUNK_SECONDS_DEFAULT)
            )
        except Exception as ex:
            self.logger.error("Error loading Kaltura Caption loader %s", ex)
        return caption_loader
