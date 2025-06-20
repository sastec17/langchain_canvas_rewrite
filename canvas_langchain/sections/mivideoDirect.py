"""Grabs relevant video mediaIds from canvas (security) & uses mivideoDirect"""
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
        self.headers: Dict[str, str] = {
            'Authorization': self._getAuthToken()}
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
            mivideo_id_list = self._get_media_ids() if mivideo_id is None else [mivideo_id]
            
            # extract media entries for metadata 
            self.mediaFilter.idIn = ','.join(mivideo_id_list)
            mediaEntries = self.client.media.list(self.mediaFilter)
            mediaMapping = {entry.id:entry.name for entry in mediaEntries.objects}
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
                                'filename': mediaMapping[captionAsset.entryId],
                                'media_id': captionAsset.entryId,
                                'timestamp': str(timestamp)[0:-4],  # no ms
                                'caption_id': captionAsset.id,
                                #'language_code': captionAsset.languageCode,
                                'caption_format': 'SRT'}))
                        index += 1

        except Exception as ex:
            print(f"EXCEPTION OCCURRED: {ex}")
        
        return mivideo_documents
    
    
    def _getAuthToken(self):
        try:
            auth = f"{settings.MIVIDEO_API_AUTH_ID}:{settings.MIVIDEO_API_AUTH_SECRET}"
            authBase64 = base64.b64encode(auth.encode('utf-8')).decode('utf-8')

            # FIXME: this API raises HTTP 500 error if authSecret is incorrect
            url: str = f'https://{settings.MIVIDEO_API_HOST}/um/oauth2/token'

            params: Dict[str, str] = {'grant_type': 'client_credentials',
                                      'scope': 'mivideo'}
            headers: Dict[str, str] = {'Authorization': f'Basic {authBase64}'}
            response: requests.Response = self._requestWithRetry(
                url, method='POST', params=params, headers=headers)
            response.raise_for_status()

            tokenData: Dict[str, Any] = response.json()
            self.logger.logStatement(f'_getAuthToken {response.elapsed.total_seconds()}s', 'DEBUG')
            return f"{tokenData['token_type']} {tokenData['access_token']}"

        except Exception as e:
            self.logger.logStatement("Failed to get authZ token: {z}", "ERROR")            
            raise


    def _requestWithRetry(self, url: str, method: str = 'GET',
                          params: Dict[str, Any] = {},
                          headers: Dict[str, str] = {}) -> requests.Response:

        # requestID logged on server and used for debugging
        requestId = str(uuid.uuid4())
        headers['X-Request-Id'] = requestId
        try:
            #TODO: USE TIMEOUT VAR INSTEAD OF 2
            response: requests.Response = requests.request(
                method, url, params=params, headers=headers,
                timeout=2)
            response.raise_for_status()
            return response
        except Timeout as e:
            self.logger.logStatement(f'Request "{url}" timed out: {e};'
                           f' requestId: {requestId}', 'ERROR')
            raise
        except (HTTPError, Timeout, RequestException) as e:
            self.logger.logStatement(f'Request failed: {e}; requestId: {requestId}', 'ERROR')
            raise
        except Exception as e:
            self.logger.logStatement(f'An unexpected error occurred: {e};'
                         f' requestId: {requestId}', 'ERROR')
            raise


    def _get_media_ids_direct(self) -> List[str]:
        try:
            filter = KalturaCategoryFilter()
            filter.fullNameIn = "Canvas_Umich>Site>Channels>429432>inContext"
            pager = KalturaFilterPager()
            result = self.client.category.list(filter, pager)
            print(result)

        except Exception as e:
            self.logger.logStatement(message=f"Exception while getting media ids: {e}", level="ERROR")


    def _get_media_ids(self) -> List[str]:
        try:
            url = f"{self.baseUrl}/course/{self.course.id}/media"
            # TODO: Get userId - can move up for runtime purposes
            userId = str('813788')
            params = {'pageIndex': 1, 'pageSize': 500}
            headers = {'LMS-User-Id': userId, **self.headers}
            response = self._requestWithRetry(url=url, params=params, headers=headers)
            self.logger.logStatement(f'getMediaList {response.elapsed.total_seconds()}s', "DEBUG")
            response.raise_for_status()
        except Exception as e:
            self.logger.logStatement(message=f"Exception while getting media ids: {e}", level="ERROR")

        return [obj['id'] for obj in response.json().get('objects', [])]
