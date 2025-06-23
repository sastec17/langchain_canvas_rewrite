import os

from canvas_langchain.canvas import CanvasLoader

try:
    from django.conf import settings
except ImportError as err:
        import settings


loader = CanvasLoader(
    api_url=getattr(settings, 'TEST_CANVAS_API_URL', 'https://umich.instructure.com'),
    api_key=settings.TEST_CANVAS_API_KEY,
    course_id=int(settings.TEST_CANVAS_COURSE_ID),
)

try:
    documents = loader.load()

    print("\nDocuments:\n")
    print('\n\n'.join(map(repr, documents)))

    print("\nInvalid files:\n")
    print(loader.invalid_files)

    print("\nErrors:\n")
    print(loader.logger.errors)

    print("\nIndexed:\n")
    print(sorted(loader.indexed_items))

except Exception as ex:
    print(loader.get_details('DEBUG'))
    print(ex)
