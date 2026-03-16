import re
import requests
import os
from bs4 import BeautifulSoup
from time import sleep
import warnings
from bs4.builder import XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
from headers import get_random_headers

RETRY_FAILED_SITES = True
SITEMAP_URL = "https://eecs.berkeley.edu/sitemap_index.xml"
HTML_STORAGE_URL = os.path.join(os.path.dirname(__file__), "crawled_html")
SLEEP_TIME = 1  # 10 seconds

sites_to_visit = []
sites_visited = set()
ignored_links = []
failed_links = []

EECS_URL_PATTERN = re.compile(
    r"https?:\/\/(?:www\d*\.)?eecs\.berkeley\.edu(?:\/[^\s]*)?"
)


def should_visit_link(url):
    return bool(
        EECS_URL_PATTERN.fullmatch(url) 
        and url not in sites_visited
        and not url.lower().endswith(".pdf")
        and not url.lower().endswith(".jpeg")
        and not url.lower().endswith(".jpg")
        and not url.lower().endswith(".png")
        )


def get_html(url) -> string:
    try:
        response = requests.get(url, headers= get_random_headers())
        return response.status_code, response.text
    except Exception as e:
        print(e)
        return None, None


def extract_links(html):
    try:
        soup = BeautifulSoup(html, "html.parser")
        links = soup.find_all("a", href=True)

        sitemap_links = soup.find_all("loc")
        sitemap_urls = [link.text for link in sitemap_links]
        # TODO: extract links from HTML
        all_links = [link["href"] for link in links] + sitemap_urls
        return [link for link in all_links if should_visit_link(link)]
    except Exception as e:
        print(e)
        return []


def cache_sites_progress():
    with open(os.path.join(HTML_STORAGE_URL, "visited_sites.txt"), "w") as f:
        f.write("\n".join(sites_visited))
    with open(os.path.join(HTML_STORAGE_URL, "ignored_links.txt"), "w") as f:
        f.write("\n".join(ignored_links))
    with open(os.path.join(HTML_STORAGE_URL, "failed_links.txt"), "w") as f:
        f.write("\n".join(failed_links))
    with open(os.path.join(HTML_STORAGE_URL, "sites_to_visit.txt"), "w") as f:
        f.write("\n".join(sites_to_visit))


def load_sites_progress():
    """Load cached progress from previous run. Returns True if cache was loaded."""
    global sites_to_visit, sites_visited, ignored_links, failed_links
    visited_path = os.path.join(HTML_STORAGE_URL, "visited_sites.txt")
    if not os.path.exists(visited_path):
        return False

    def _read_lines(filename):
        path = os.path.join(HTML_STORAGE_URL, filename)
        if os.path.exists(path):
            with open(path, "r") as f:
                return [line for line in f.read().splitlines() if line]
        return []

    sites_visited = set(_read_lines("visited_sites.txt"))
    ignored_links = _read_lines("ignored_links.txt")
    failed_links = _read_lines("failed_links.txt")
    sites_to_visit = _read_lines("sites_to_visit.txt")
    print(f"Resumed from cache: {len(sites_visited)} visited, {len(sites_to_visit)} queued, {len(failed_links)} failed.")
    return True


def setup_folders():
    if not os.path.exists(HTML_STORAGE_URL):
        os.makedirs(HTML_STORAGE_URL)


def crawl():
    load_sites_progress()
    if RETRY_FAILED_SITES:
        print("failed_links:", failed_links)
        sites_to_visit.extend(failed_links)
        os.remove(os.path.join(HTML_STORAGE_URL, "failed_links.txt"))
    else:
        sites_to_visit.append(SITEMAP_URL)

    while len(sites_to_visit) > 0:
        sleep(SLEEP_TIME)
        print(
            f"Visited {len(sites_visited)} sites. {len(sites_to_visit)} sites to visit. Ignored {len(ignored_links)} links."
        )
        cache_sites_progress()
        site = sites_to_visit.pop()
        if os.path.exists(get_file_path_from_site(site)):
            print(f"Skipping {site} as it has already been visited.")
            print(f"File path: {get_file_path_from_site(site)}")
            continue
        sites_visited.add(site)
        status_code, html = get_html(site)
        if status_code != 200:
            print(f"Failed to fetch {site}: {status_code}")
            failed_links.append(site)
            continue
        with open(get_file_path_from_site(site), "w") as f:
            f.write(html)
        links = extract_links(html)
        sites_to_visit.extend(links)

def get_file_path_from_site(site_url):
    return os.path.join(HTML_STORAGE_URL, site_url.replace("/", "_"))

if __name__ == "__main__":
    setup_folders()
    crawl()
