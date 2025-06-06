# Canvas LangChain document loader

## Features

Indexes Canvas Modules, Pages, Announcements, Assignments, and Files

The following file types are supported:
`md` `htm` `html` `docx` `xls` `xlsx` `pptx` `pdf` `rtf` `txt` `csv`

(`doc` support would require libreoffice, so has not been implemented in this library)

If a course has a MiVideo "Media Gallery" available, the loader will
also index the captions of the media in the gallery. At this time, the loader
does not index captions of media embedded in Canvas Pages or other content.

## Running with Canvas and Maizey

### Configure environment
Add the following variables to `.env` in umgpt from .env.example in this repo:
```
MIVIDEO_API_HOST='gw.api.it.umich.edu'
MIVIDEO_API_AUTH_ID=<AUTH ID>
MIVIDEO_API_AUTH_SECRET=<AUTH SECRET>

MIVIDEO_SOURCE_URL_TEMPLATE='https://www.mivideo.it.umich.edu/media/t/{mediaId}?st={startSeconds}'
CANVAS_COURSE_URL_TEMPLATE='https://umich.instructure.com/courses/{courseId}/external_tools/53084' #53084 indicates MIVIDEO
CANVAS_USER_ID_OVERRIDE_DEV_ONLY=<OVERRIDE KEY>

# The following are optional
MIVIDEO_LANGUAGE_CODES_CSV='en-us,en'
MIVIDEO_CHUNK_SECONDS='120'
```

Reach out to sastec or lsloan for auth secrets. 

### Connect to canvas-langhcain
In UMGPT, run the following: 
```
git pull
git checkout GPT-1470-canvas-testing

# Verify dependencies are correct
poetry lock 

# Update docker container - refresh libraries
docker-compose up --build --force-recreate
```

Note - `poetry lock` may require python3.12 - I recommend downloading python 3.12.10 and creating a virtual environment as follows:
```
python3.12 -mvenv .venv
source .venv/bin/activate
```

#### Using local canvas-langchain library
Note, this will use the remote version of canvas-langchain by default. 

If you wish to develop locally within umgpt, I recommend the following:

1.  Download this repository into a folder called 'canvas-langchain' within root UMICHGPT folder (The parent canvas-langchain folder should be at the same level as `t1/` and `t2/`)
2. Modify pyproject.toml's canvas-langchain dependency to read 
	```
	canvas-langchain = { path="canvas-langchain", develop=true }
	```
3. Run the following on command line:
	```
	# Verify dependencies & libraries are correct
	poetry lock 

	# Update docker container - refresh libraries
	docker-compose up --build --force-recreate
	```
### Connect to Canvas

#### The first time... 
1. In Canvas course, inspect the `UM-Maizey` option on the sidebar via dev-tools. 
2. Copy the href element associated with this button
3. Open a separate browser window and open the inspector tools to the `Network` tab.
4. Paste href link into browser and search. This will redirect to the production version of Maizey + will likely throw an indexing or payment-related error. 
5. In the network tab, search for "canvaslink" - There should be an entry like this `https://umgpt.umich.edu/t2/canvaslink?....`. Copy the entire link and modify the beginning to start with `https://<UNIQNAME>.ngrok.io/t2/canvaslink?....`
6. Paste this link into the browser and enjoy local testing!


#### Further testing
After connecting your Canvas course to Maizey, you'll just need to reindex the course to test the canvas-langchain library. 

In Maizey, select your project. Under "Project Details" - Click "reindex".

Feedback should appear in terminal. Please add debug / print statements as needed.

## Running locally (development)

You can build/run the provided Dockerfile, or install dependencies as described below

### Configure Environment

This environment may be used with Docker or without.

Create a `.env` file in the root of the project by copying the `.env.example`
file.

```bash
cp .env.example .env
```

Edit the new `.env` file to fill in the correct values. Refer to the comments
in the `.env` file for more information.

> #### 🔔 Important
> Do not set the `CANVAS_USER_ID_OVERRIDE_DEV_ONLY` variable in a production
> environment or other shared environment. It is only for development purposes.

### Running independently with Python Virtual Environment 

#### Create a Python Virtual Environment
```bash
python -mvenv .venv
. .venv/bin/activate
```

#### Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements-dev.txt
```

#### Run

```bash
python canvas-test.py
```

### Running independently with Docker (Not yet tested by @sastec17 with updated code)

The following command builds a Docker image named `ldc_dev` containing Python,
all the required dependencies, and the project code, then runs it.

```bash
docker build -t ldc_dev . && docker run -it ldc_dev
```

## Usage example

> #### 💡 Note
> See the `canvas-test.py` file for a more complete example.

```python
from canvas_langchain.canvas import CanvasLoader

loader = CanvasLoader(
	api_url="https://CANVAS_API_URL_GOES_HERE",
	api_key="CANVAS_API_KEY_GOES_HERE",
	course_id=int(CANVAS_COURSE_ID_GOES_HERE),
)

try:
	documents = loader.load()

	print("\nDocuments:\n")
	print(documents)

	print("\nInvalid files:\n")
	print(loader.invalid_files)
	print("")

	print("\nErrors:\n")
	print(loader.errors)
	print("")

	print("\nIndexed:\n")
	print(loader.indexed_items)
	print("")

	print("\nProgress:\n")
	print(loader.get_details('DEBUG'))
	print("")
except Exception:
	details = loader.get_details('DEBUG')
```

If errors are present, `loader.errors` will contain one list element per error. It will consist of an error message (key named `message`) and if the error pertains to a specific item within canvas, it will list the `entity_type` and the `entity_id` of the resource where the exception occurred.
