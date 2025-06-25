"""Just loads all videos from Kaltura directly - No access / published checks."""
from typing import List
from requests.exceptions import RequestException, HTTPError, Timeout
from langchain.docstore.document import Document

# Kaltura Caption Loader
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
        self.baseUrl: str = f'https://{settings.MIVIDEO_API_HOST}/um/aa/mivideo/v1'
        self.client = KalturaClient(KalturaConfiguration())
        self.client.setKs(settings.KALTURA_NEW_SESSION)
        # filters
        self.mediaFilter = KalturaMediaEntryFilter()
        self.captionFilter = KalturaCaptionAssetFilter()
        self.categoryFilter = KalturaCategoryFilter()
        self.pager = KalturaFilterPager()

        self.timeout: int = 2
        self.chunkSeconds = 120
        self.urlTemplate = settings.MIVIDEO_SOURCE_URL_TEMPLATE

    # Keep mivideo_id parameter to easily switch versions for testing - TODO: remove later
    def load(self, mivideo_id: None) -> List[Document]:
        self.logger.logStatement(message="Loading MiVideo directly...", level="INFO")
        try:
            mivideo_documents = []

            # Extract parent ID for course
            self.categoryFilter.fullNameIn = f"Canvas_Umich>Site>Channels>{self.course.id}>inContext"
            result = self.client.category.list(self.categoryFilter, self.pager)
            totalNumEntries = result.totalCount

            # Extract all videos for course
            if totalNumEntries == 0:
                 return mivideo_documents
            self.mediaFilter.categoriesIdsMatchAnd = result.objects[0].parentId
            mediaEntries = self.client.media.list(self.mediaFilter, self.pager)

            if mediaEntries.totalCount == 0:
                self.mediaFilter.categoriesIdsMatchAnd = result.objects[0].id
                mediaEntries = self.client.media.list(self.mediaFilter, self.pager)

            assert(mediaEntries.totalCount != totalNumEntries), "No media entries found for the course."

            mediaMapping = {entry.id:entry.name for entry in mediaEntries.objects}
            mivideo_id_list = [entry.id for entry in mediaEntries.objects]
            # Extract captions for each video
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
                                'filename': mediaMapping[captionAsset.entryId],
                                'media_id': captionAsset.entryId,
                                'timestamp': str(timestamp)[0:-4],  # no ms
                                'caption_id': captionAsset.id,
                                #'language_code': captionAsset.languageCode,
                                'caption_format': 'SRT'}))
                        index += 1
        except Exception as e:
             self.logger.logStatement(message=f"Error loading videos {e}", level="DEBUG")
        return mivideo_documents
