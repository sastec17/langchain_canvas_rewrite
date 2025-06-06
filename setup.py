from setuptools import setup, find_packages

setup(
    name="canvas_langchain",
    version="0.9.18",
    description="A canvas langchain integration",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="University of Michigan",
    author_email="noreply@umich.edu",
    url="https://github.com/umich-its-ai/langchain-doc-canvas",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: GNU General Public License (GPL)",
    ],
    install_requires=[
        "langchain",
        "langchain-community",
        "unstructured[docx,pptx]",
        "canvasapi==3.3.0",
        "beautifulsoup4",
        "lxml",
        "PyPDF2[crypto]",
        "docx2txt",
        "striprtf",
        "pandas",
        "pydantic",
        "openpyxl",
        "xlrd",
        "markdown",
        "pytz",
        'LangChainKaltura @ git+https://github.com/tl-its-umich-edu/langchain_kaltura@2025.03.01#egg=LangChainKaltura'
    ],
    python_requires=">=3.8.1",
)
