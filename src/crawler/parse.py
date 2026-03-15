import os
from bs4 import BeautifulSoup
from bs4.builder import XMLParsedAsHTMLWarning
import warnings

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
CRAWLED_PATH = os.path.join(os.path.dirname(__file__), "crawled_html")
PARSED_DOCUMENTS_PATH = os.path.join(os.path.dirname(__file__), "parsed_documents")

TAGS_TO_REMOVE = ["script", "style", "nav", "footer", "header", "aside", "noscript"]
DIVS_TO_REMOVE = ["pagination","post__meta", "notice-content"]
IGNORE_LIST = [
    "failed_links.txt",
    "visited_links.txt",
    "ignored_links.txt",
]
IGNORE_FORMATS = [
    # "doc",
    # "docx",
    # "edu",
    # "edu_",
    # "edu_ACG_",
    # "edu_Gier",
    # "edu_IPRO_",
    # "edu_about",
    # "edu_blog",
    # "edu_blog_",
    # "edu_book_",
    # "edu_cs_",
    # "edu_csa",
    # "edu_de_",
    # "edu_ee_",
    # "edu_news",
    # "edu_news_",
    # "edu_~hu_",
    # "edu_~yss_",
    # "htm",
    # "htm#CIR",
    # "htm#CPSDA",
    # "htm#EM",
    # "htm#IDNCS",
    # "htm#INC",
    # "htm#MEMS",
    # "htm#OPTO",
    # "htm#POW",
    # "htm#SD",
    # "htm#SP",
    # "htm#SPT",
    # "html",
    # "html#2",
    # "html#g_16",
    # "html#g_6",
    "jpg",
    "pdf",
    "png",
    "ppsx",
    "ppt",
    "pptx",
    # "shtml",
    # "txt",
    # "wmv",
    # "xml",
]


def list_file_formats():
    from collections import defaultdict

    formats = defaultdict(int)
    for file in os.listdir(CRAWLED_PATH):
        if file[-10:].find(".") != -1:
            format = file.split(".")[-1]
            formats[format] += 1
    return formats

def get_file_format(file):
    if file[-10:].find(".") != -1:
        return file.split(".")[-1]
    return None

def get_crawled_files():
    files = [
        file
        for file in os.listdir(CRAWLED_PATH)
        if file not in IGNORE_LIST
        and get_file_format(file) not in IGNORE_FORMATS
        # and file.find("memorial-sculpture") != -1
        # and file.find("2022") != -1
    ]
    yield from files


def parse():
    for file in get_crawled_files():
        html = None
        with open(os.path.join(CRAWLED_PATH, file), "r") as f:
            html = f.read()
        if not html:
            continue
        text,filtered_html = extract_text(html)
        text = remove_extra_newlines(text)
        with open(os.path.join(PARSED_DOCUMENTS_PATH, file), "w") as f:
            f.write(text)
        # with open(os.path.join(PARSED_DOCUMENTS_PATH, file + ".html"), "w") as f:
        #     f.write(str(filtered_html))

def setup_folders():
    if not os.path.exists(PARSED_DOCUMENTS_PATH):
        os.makedirs(PARSED_DOCUMENTS_PATH)

def extract_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in TAGS_TO_REMOVE:
        for element in soup.find_all(tag):
            element.decompose()
    for div in DIVS_TO_REMOVE:
        for element in soup.find_all("div", class_=div):
            element.decompose()
    return soup.get_text(), soup

def remove_extra_newlines(text):
    return "\n".join([line for line in text.split("\n") if line.strip()])

if __name__ == "__main__":
    setup_folders()
    parse()
