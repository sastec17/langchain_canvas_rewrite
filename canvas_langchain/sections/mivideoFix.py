"""Just loads all videos from Kaltura directly - No access / published checks."""
from typing import List, Dict, Any
from requests.exceptions import RequestException, HTTPError, Timeout
from langchain.docstore.document import Document

# Kaltura Caption Loader
import uuid
import base64
import pysrt
import requests
from KalturaClient import KalturaClient, KalturaConfiguration
from KalturaClient.Plugins.Core import (KalturaSessionType, KalturaMediaEntry,
    KalturaMediaEntryFilter, KalturaFilterPager, KalturaCategoryFilter)
from KalturaClient.Plugins.Caption import (KalturaCaptionAsset,
    KalturaCaptionAssetFilter)
# compatible with isolated and integrated testing
try:
    from django.conf import settings
except ImportError as err:
        import settings

class MiVideoLoader():
    def __init__(self, canvas, course, indexed_items, logger):
        self.canvas = canvas
        self.course = course
        self.indexed_items = indexed_items
        self.logger = logger
        self.caption_loader = None
        self.baseUrl: str = f'https://{settings.MIVIDEO_API_HOST}/um/aa/mivideo/v1'
        self.mivideo_authorized = True
        self.client = KalturaClient(KalturaConfiguration())
        self.client.setKs(settings.KALTURA_APP_SESSION)
        self.mediaFilter = KalturaMediaEntryFilter()
        self.captionFilter = KalturaCaptionAssetFilter()
        self.mediaMapping = {}
        self.mediaEntries = self._get_media_content()
        # TODO:Make much cleaner
        self.timeout: int = 2
        self.chunkSeconds = 120
        #TODO: move to settings
        self.urlTemplate = 'https://www.mivideo.it.umich.edu/media/t/{mediaId}?st={startSeconds}'


    def load(self, mivideo_id: str | None) -> List[Document]:
        """Load MiVideo media captions"""
        self.logger.logStatement("Loading MiVideo...", "INFO")
        mivideo_documents = []
        try: 
            # Get mivideo_id_list
            #mivideo_id_list = self._get_media_ids_direct() if mivideo_id is None else [mivideo_id]
            mivideo_id_list = [entry.id for entry in self.mediaEntries]

            # extract captions
            self.captionFilter.entryIdIn = ','.join(mivideo_id_list)
            captionAssets = self.client.caption.captionAsset.list(self.captionFilter)

            for captionAsset in captionAssets.objects:
                captionUrl = self.client.caption.captionAsset.getUrl(captionAsset.id)
                text = pysrt.from_string(requests.get(captionUrl).text)
                
                index = 0
                while (captionsSection := text.slice(
                        starts_after={'seconds': (start := self.chunkSeconds * index)},
                        ends_before={'seconds': start + self.chunkSeconds})):

                        timestamp = captionsSection[0].start
                        mivideo_documents.append(Document(
                            page_content=captionsSection.text,
                            metadata={
                                # Start time is sliced to remove milliseconds.
                                'source': self.urlTemplate.format(
                                    mediaId=captionAsset.entryId,
                                    startSeconds=timestamp.ordinal // 1000),
                                'filename': self.mediaMapping[captionAsset.entryId],
                                'media_id': captionAsset.entryId,
                                'timestamp': str(timestamp)[0:-4],  # no ms
                                'caption_id': captionAsset.id,
                                #'language_code': captionAsset.languageCode,
                                'caption_format': 'SRT'}))
                        index += 1

        except Exception as ex:
            print(f"EXCEPTION OCCURRED: {ex}")
        
        return mivideo_documents
    

    def _get_media_content(self) -> List[str]:
        try:
            # get category for filtering
            filter = KalturaCategoryFilter()
            # TODO: TEMPLATE THIS
            filter.fullNameIn = f"Canvas_Umich>Site>Channels>{self.course.id}>inContext"
            pager = KalturaFilterPager()
            print("HERE")
            result = self.client.category.list(filter, pager)
            if result and result[0]:
                self.mediaFilter.categoryAncestorIdIn = result[0].parentId
                self.mediaEntries = self.client.media.list(filter, pager)
                self.mediaMapping = {entry.id:entry.name for entry in self.mediaEntries.objects}

        except Exception as e:
            self.logger.logStatement(message=f"Exception while getting media ids: {e}", level="ERROR")

