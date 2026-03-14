import re
import requests
import os
from bs4 import BeautifulSoup
from time import sleep
import warnings                                                                                          
import warnings;from bs4.builder import XMLParsedAsHTMLWarning;
warnings.filterwarnings('ignore', category=XMLParsedAsHTMLWarning)

SITEMAP_URL = "https://eecs.berkeley.edu/2022/12/berkeley-eecs-to-honor-joseph-gier-with-memorial-sculpture/"
HTML_STORAGE_URL = os.path.join(os.path.dirname(__file__), "crawled_html")
SLEEP_TIME = 10  # 10 seconds

sites_to_visit = []
sites_visited = set()
ignored_links = []
failed_links = []

EECS_URL_PATTERN = re.compile(r"https?:\/\/(?:www\d*\.)?eecs\.berkeley\.edu(?:\/[^\s]*)?")

def should_visit_link(url):
    return bool(
        EECS_URL_PATTERN.fullmatch(url)
        and url not in sites_visited
    )

def get_html(url):
    response = requests.get(url)
    return response.status_code, response.text

def extract_links(html):
    soup = BeautifulSoup(html, 'html.parser')
    links = soup.find_all("a", href=True)

    sitemap_links = soup.find_all("loc")
    sitemap_urls = [link.text for link in sitemap_links]
    # TODO: extract links from HTML
    all_links = [link['href'] for link in links] + sitemap_urls
    return [link for link in all_links if should_visit_link(link)]

def cache_sites_progress():
    with open(os.path.join(HTML_STORAGE_URL, "visited_sites.txt"), "w") as f:
        f.write("\n".join(sites_visited))
    with open(os.path.join(HTML_STORAGE_URL, "ignored_links.txt"), "w") as f:
        f.write("\n".join(ignored_links))
    with open(os.path.join(HTML_STORAGE_URL, "failed_links.txt"), "w") as f:
        f.write("\n".join(failed_links))
    with open(os.path.join(HTML_STORAGE_URL, "sites_to_visit.txt"), "w") as f:
        f.write("\n".join(sites_to_visit))

def setup_folders():
    if not os.path.exists(HTML_STORAGE_URL):
        os.makedirs(HTML_STORAGE_URL)

def crawl():
    sites_to_visit.append(SITEMAP_URL)

    while len(sites_to_visit) > 0:
        print(f"Visited {len(sites_visited)} sites. {len(sites_to_visit)} sites to visit. Ignored {len(ignored_links)} links.")
        cache_sites_progress()
        sleep(SLEEP_TIME)
        site = sites_to_visit.pop()
        sites_visited.add(site)
        status_code, html = get_html(site)
        if status_code != 200:
            print(f"Failed to fetch {site}: {status_code}")
            failed_links.append(site)
            continue
        with open(os.path.join(HTML_STORAGE_URL, site.replace("/", "_")), "w") as f:
            f.write(html)
        links = extract_links(html)
        sites_to_visit.extend(links)

if __name__ == "__main__":
    setup_folders()
    crawl()
