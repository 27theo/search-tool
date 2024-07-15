# A Search Tool

This is an upload of a coursework assignment I completed during my degree @
UoL. The software product consists of a primitive scraping tool that builds an
index of a simple site. The index can then be searched through, results sorted
by a simple ranking algorithm.

## Report

### 1. The crawler

I define two global variables, a base url BASE_URL and a domain DOMAIN. The
base url denotes the index of the site, which is also used as the start page:
https://quotes.toscrape.com.

The domain denotes the domain that the scrape is confined to:
quotes.toscrape.com.

The scrape starts at the base url. The requests library from the standard
library is used to GET request each page. A politeness window of 6 seconds is
observed - no request will be made within 6 seconds of another request. The
crawler maintains a queue of urls to visit, and a list of previously seen urls.
Each page is scanned for each <a> element, and the "href" attribute is
extracted. I use the urllib.parse.urljoin function from the standard library to
concatenate BASE_URL and the extracted link. This has a handy effect - if the
extracted link is a link to a different domain, urljoin returns that different
domain. Else, if the extracted link is an internal link or a link to a site on
the scrape domain, urljoin returns a link to the page on the scrape domain. It
also formats urls, removing any need to check for trailing slashes. Therefore,
the next step is to check whether the url is external (i.e. to google/twitter…)
or whether we have already visited it. If neither of these conditions apply,
the url is added to the queue to be scraped later.

After the crawler iterates over each <a> element, the words on the active page
are tokenised. The get_text method from Beautiful Soup is used to retrieve all
the text on the page. A regex is then applied to retrieve all words delimited
by word boundaries from the text: "\b\w+\b". The results are formatted to
lowercase. Any stop words are then filtered out, from the global table
STOPWORDS. The list of tokens is then written to the inverted index, as
described below (2. Inverted index).

The crawler moves through each link in the queue of urls in the order of
discovery, until all the pages on the scrape domain exposed by <a> elements in
the visited pages are exhausted, and the inverted index has been fully built.

The inverted index is then written to the file system, as described below.

Appropriate error handling and reporting is applied throughout.

### 2. The inverted index

The inverted index takes the form of a python dictionary. Each key is a tokens
(or words) and each value is a list of strings that represent an appearance of
that word: each a URL and an integer position, delimited by a pipe character
'|'. For example, the following would denote that the word computer is found at
page1, position 28, and page2, position 9.

```py
INDEX["computer"] = [ "site.com/page1|28", "site.com/page2|9" ]
```

For storage, the dictionary is serialised into JSON using the json library from
the Python standard library. That is, the json.dumps method converts the
dictionary and all its contents to a string, which is written to a file in the
working directory "index.json". Similarly, the inverted index is loaded from
the file using the json.loads method, reading the data from the "index.json"
file if it exists (this is checked and handled appropriately).

### 3. The ranking method

The inverted index is transformed into a mapping of pages to word occurrences,
only tracking the words that are input to the find command as the search query.
For example, in a search for "super Jane Austen", where those words all occur
in page 1 at positions 48, 9, 10:

```py
page_words["site.com/page1"] = [ ("Jane", 9), ("Austen", 10), ("Super", 48) ]
```

Then for each page, three values are calculated. The first "words_hit" is how
many of the search terms the active page contains. The second "n_occurences" is
the number of appearances of all the search words summed together. The third
"adjacencies" is how many times a pair of distinct search words appears next to
each other (for the example above, this value would be 1, for the "Jane Austen"
combination).

My method depends on the ability in Python to be able to rank based on multiple
values, through the use of a tuple. The results are first sorted on the first
value. Within the categories denoted by the first value, the results are then
sorted on the second value. Then, a third value can be used to sort the values
within the categories denoted by the second value, and so on. As such, the
results are sorted by "words_hit", "n_occurences" and "adjacencies" in that
order. These ranked results are then displayed to the user.
