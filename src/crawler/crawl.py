import re
import requests
import os
from bs4 import BeautifulSoup
from time import sleep
import psycopg                                                                                          
import warnings
from bs4.builder import XMLParsedAsHTMLWarning;
warnings.filterwarnings('ignore', category=XMLParsedAsHTMLWarning)
from google.cloud import storage

SITEMAP_URL = "https://eecs.berkeley.edu/2022/12/berkeley-eecs-to-honor-joseph-gier-with-memorial-sculpture/"
HTML_STORAGE_URL = os.path.join(os.path.dirname(__file__), "crawled_html")
SLEEP_TIME = 10  # 10 seconds
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

def connect_to_database():
    database_host = os.getenv("DATABASE_HOST")
    database_port = os.getenv("DATABASE_PORT")
    database_name = os.getenv("DATABASE_NAME")
    database_user = os.getenv("DATABASE_USER")
    database_password = os.getenv("DATABASE_PASSWORD")
    conn = psycopg.connect(
        host=database_host,
        port=database_port,
        dbname=database_name,
        user=database_user,
        password=database_password
    )
    return conn

def get_bucket_connection():
    bucket_name = os.getenv("BUCKET_NAME")
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    return bucket

def get_some_sites_to_visit(db_connection) -> list[str]:
    db_connection.cursor().execute("SELECT url FROM sites_to_visit LIMIT 10 where status = 'to_visit'")
    return [row[0] for row in db_connection.cursor().fetchall()]

def mark_link_as_failed(db_connection, url: str, status_code: int):
    db_connection.cursor().execute("UPDATE sites_to_visit SET status = 'failed', error_code = %s WHERE url = %s", (status_code, url))
    db_connection.commit()

def mark_site_as_visited(db_connection, url: str):
    db_connection.cursor().execute("UPDATE sites_to_visit SET status = 'visited' WHERE url = %s", (url,))
    db_connection.commit()

def create_new_site_links(db_connection, links: list[str]):
    for link in links:
        db_connection.cursor().execute("INSERT INTO sites_to_visit (url, status) VALUES (%s, 'to_visit')", (link,))
    db_connection.commit()

def store_html(bucket, site_name, html):
    blob = bucket.blob(site_name)
    # The destination_blob_name can include a prefix to simulate folder structure
    blob.upload_from_string(html, content_type='text/plain')
    print(f"Uploaded to gs://{BUCKET_NAME}/{site_name}")


def crawl():
    conn = connect_to_database()
    bucket = get_bucket_connection()
    sites_to_visit = get_some_sites_to_visit(conn)
    print("visiting sites:", '\n'.join(sites_to_visit))
    while len(sites_to_visit) > 0:
        site = sites_to_visit.pop()
        status_code, html = get_html(site)
        if status_code != 200:
            print(f"Failed to fetch {site}: {status_code}")
            mark_link_as_failed(conn, site, status_code)
            continue
        mark_site_as_visited(conn, site)
        site_name = site.replace("https://", "").replace("http://", "").replace("/", "_")
        store_html(bucket, site_name, html)
        links = extract_links(html)
        create_new_site_links(conn, links)
        sleep(SLEEP_TIME)

if __name__ == "__main__":
    crawl()
