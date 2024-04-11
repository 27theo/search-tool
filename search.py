"""
Client application.
--
Theo Addis <sc21tcda@leeds.ac.uk>
"""

from requests import Session
from bs4 import BeautifulSoup
from collections import defaultdict
import re
import json
import time

URL = "https://quotes.toscrape.com"
RATE_LIMIT = 6
DEBUG = True
INDEX: defaultdict = defaultdict(list)
INDEX_FILE = "index.json"

def debug(output: str) -> None:
    if DEBUG: print(output)

def build() -> None:
    current_page = URL
    queued_pages = [current_page]
    seen_pages = []
    session = Session()
    last_request_at = 0
    debug("[ ] Starting site-wide scrape")

    # Scrape the site, building the inverted index
    while True:
        try: current_page = queued_pages.pop()
        except IndexError: break
        debug(f"[ ] Scraping {current_page}")
        seen_pages.append(current_page)

        # Fetch the current page with a request
        try:
            # We observe a rate limit before requesting
            while time.time() - last_request_at < RATE_LIMIT:
                time.sleep(0.1)
            last_request_at = time.time()
            response = session.get(current_page)
            if response.status_code != 200:
                debug(f"[W] Got {response.status_code} code from {current_page}")
                continue
        except Exception as e:
            debug(f"[E] Got {e} attempting to retrieve {current_page}")
            continue

        # Fetch the next link if there is one
        soup = BeautifulSoup(response.content, "html.parser")
        next_item = soup.find("li", attrs={"class": "next"})
        if next_item:
            next_link = getattr(next_item, "a", None)
            if next_link and next_link.has_attr("href"):
                href = URL + next_link["href"]
                if href not in seen_pages:
                    seen_pages.append(href)
                    queued_pages.append(href)

        # Tokenize the page and write it to the inverted index
        text = soup.get_text()
        tokens = re.findall(r"\b\w+\b", text.lower())
        for token in tokens:
            if current_page not in INDEX[token]:
                INDEX[token].append(current_page)

    # Save the inverted index to a file
    with open(INDEX_FILE, "w") as file:
        json.dump(INDEX, file)

def load() -> None:
    global INDEX
    try:
        with open(INDEX_FILE, "r") as file:
            INDEX = json.load(file)
        print(f"Index read from file '{INDEX_FILE}', {len(INDEX.keys())} words indexed.")
    except FileNotFoundError:
        print(f"No index file found at '{INDEX_FILE}'. Build it with the 'build' command.")

def print_(word: str) -> None:
    if word not in INDEX:
        print(f"Search term '{word}' not found in index.")
        return
    print(INDEX[word])

def find(words: list[str]) -> None:
    word = words[0]
    if word not in INDEX:
        print(f"Search term '{word}' not found in index.")
        return
    print(f"Search term '{word}' appears at:")
    for i, url in enumerate(INDEX[word]):
        if i == len(INDEX[word]) - 1:
            print(f"└ {url}")
        else:
            print(f"├ {url}")

def help() -> None:
    print("\n"
          "    build\n"
          "    load\n"
          "    print [word]\n"
          "    find [words]\n"
          "    exit\n")

def main() -> None:
    # Enter main input loop
    while True:
        try:
            command = input("> ").lower().split()
            if command[0] == "help":
                help()
            elif command[0] == "build":
                build()
            elif command[0] == "load":
                load()
            elif command[0] == "print":
                if len(command) < 2:
                    print("Usage: print [word]")
                else:
                    print_(command[1])
            elif command[0] == "find":
                if len(command) < 2:
                    print("Usage: find [words]")
                else:
                    find(command[1:])
            elif command[0] == "exit" or command[0] == "quit":
                print("Goodbye.")
                break
        except KeyboardInterrupt:
            print()
            continue

if __name__ == "__main__":
    main()
