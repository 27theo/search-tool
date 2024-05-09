"""
Client application.
--
Theo Addis <sc21tcda@leeds.ac.uk>
"""

from requests import Session
from bs4 import BeautifulSoup
from collections import defaultdict
from itertools import combinations
from urllib.parse import urljoin
import re
import json
import time

BASE_URL = "https://quotes.toscrape.com"
DOMAIN = "quotes.toscrape.com"
RATE_LIMIT = 6
INDEX = defaultdict(list)
INDEX_FILE = "index.json"
PAGE_LENGTH = 40

# A copy of NLTK's list of english stop words
STOPWORDS = ["i", "me", "my", "myself", "we", "our", "ours", "ourselves",
             "you", "your", "yours", "yourself", "yourselves", "he", "him",
             "his", "himself", "she", "her", "hers", "herself", "it", "its",
             "itself", "they", "them", "their", "theirs", "themselves", "what",
             "which", "who", "whom", "this", "that", "these", "those", "am",
             "is", "are", "was", "were", "be", "been", "being", "have", "has",
             "had", "having", "do", "does", "did", "doing", "a", "an", "the",
             "and", "but", "if", "or", "because", "as", "until", "while", "of",
             "at", "by", "for", "with", "about", "against", "between", "into",
             "through", "during", "before", "after", "above", "below", "to",
             "from", "up", "down", "in", "out", "on", "off", "over", "under",
             "again", "further", "then", "once", "here", "there", "when",
             "where", "why", "how", "all", "any", "both", "each", "few",
             "more", "most", "other", "some", "such", "no", "nor", "not",
             "only", "own", "same", "so", "than", "too", "very", "s", "t",
             "can", "will", "just", "don", "should", "now"]

def build() -> None:
    """Run the build command."""
    current_page = urljoin(BASE_URL, "/")
    queued_pages = [current_page]
    seen_pages = []
    session = Session()
    last_request_at = 0
    print("[ ] Starting site-wide scrape")

    # Scrape the site, building the inverted index
    while True:
        try: current_page = queued_pages.pop()
        except IndexError: break
        print(f"[ ] Scraping {current_page}")
        seen_pages.append(current_page)

        # Fetch the current page with a request
        try:
            # We observe a rate limit before requesting
            while time.time() - last_request_at < RATE_LIMIT:
                time.sleep(0.1)
            last_request_at = time.time()
            response = session.get(current_page)
            if response.status_code != 200:
                print(f"[W] Got {response.status_code} code from {current_page}")
                continue
        except Exception as e:
            print(f"[E] Got {e} attempting to retrieve {current_page}")
            continue

        # Fetch the next link if there is one
        soup = BeautifulSoup(response.content, "html.parser")
        for link in soup.find_all("a"):
            url = urljoin(BASE_URL, link.get("href"))
            if DOMAIN not in url: continue
            # Append to the queue if not already seen
            if url not in seen_pages:
                seen_pages.append(url)
                queued_pages.append(url)

        # Tokenize the page and write it to the inverted index
        # · We find all words in the text delimited by word boundaries,
        #   building an ordered list of the words in each page
        # · We remove stop words
        # · We take the position of the word in the ordered list of
        #   words to be its position in the page, which is stored
        text = soup.get_text()
        tokens = re.findall(r"\b\w+\b", text.lower())
        tokens = [t for t in tokens if t not in STOPWORDS]
        for n, token in enumerate(tokens):
            INDEX[token].append(f"{current_page}|{n}")

    # Save the inverted index to a file
    try:
        with open(INDEX_FILE, "w") as file:
            json.dump(INDEX, file)
    except Exception as e:
        print(f"[E] Failed writing index to file: {e}")

def load() -> None:
    """Run the load command."""
    global INDEX
    try:
        with open(INDEX_FILE, "r") as file:
            INDEX = json.load(file)
        print(f"Index read from file '{INDEX_FILE}', {len(INDEX.keys())} words indexed.")
    except FileNotFoundError:
        print(f"No index file found at '{INDEX_FILE}'. Build it with the 'build' command.")

def print_(word: str) -> None:
    """Run the print command."""
    if word not in INDEX:
        print(f"Search term '{word}' not found in index.")
        return
    print(INDEX[word])

def find(words: list[str]) -> None:
    """Run the find command."""
    # Return early if none of the search terms are indexed
    if not any(word in INDEX for word in words):
        search_term = " ".join(words)
        print(f"No search terms in '{search_term}' found in index.")
        return

    # Transform the index to map pages to their words
    page_words = defaultdict(list)
    for word in words:
        if word not in INDEX: continue
        for occurence in INDEX[word]:
            page, pos = occurence.split("|")
            page_words[page].append((word, int(pos)))

    # Compile statistics for each page
    results = []
    for page, occurences in page_words.items():
        # Count how many of the search words this page has
        words_hit = len(set(o[0] for o in occurences))

        # Count how many times this page has one of the search words
        n_occurences = len(occurences)

        # Count how many times each of the words appear next to a distinct word
        adjacencies = 0
        for a, b in combinations(occurences, 2):
            # For every pair of target words present on the page...
            # If the two occurences are next to each other, count an adjacency
            if abs(a[1] - b[1]) == 1:
                adjacencies += 1

        results.append((page, words_hit, n_occurences, adjacencies))

    # Sort the results by word hits, occurences and adjacencies in that order
    ranked = sorted(results, key = lambda x: (x[1], x[2], x[3]), reverse=True)

    search_term = " ".join(words)
    print(f"Search term '{search_term}' appears at:")
    for i, url in enumerate(ranked):
        print(f"│ {i+1:3} │ {url[0]}")
        # Split into pages
        if (i + 1) % PAGE_LENGTH == 0:
            input(f"│     │ Page {(i+1)//PAGE_LENGTH}, press enter to continue...")

def help() -> None:
    """Run the help command."""
    print("  build\n"
          "  load\n"
          "  print [word]\n"
          "  find [words]\n"
          "  exit")

def main() -> None:
    """Enter main input loop."""
    while True:
        try:
            command = input("> ").lower().split()
            if len(command) == 0:
                continue
            elif command[0] == "help":
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
            elif command[0] in ["exit", "quit", "q"]:
                break
            else:
                print("Unrecognised command - see 'help' for usage.")
        except KeyboardInterrupt:
            print()
            break

if __name__ == "__main__":
    main()
