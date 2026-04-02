from __future__ import annotations

MAX_ARTICLES = 3

_DEFAULT_LANG = "en"
_DEFAULT_SORTBY = "relevance"

_TIME_DELTA_DAYS = {"day": 1, "week": 7, "month": 30}

SOURCE_LEAN_LOOKUP: dict[str, str] = {
    "cnn.com": "left",
    "msnbc.com": "left",
    "nytimes.com": "left",
    "washingtonpost.com": "left",
    "theguardian.com": "left",
    "huffpost.com": "left",
    "vox.com": "left",
    "npr.org": "left",
    "foxnews.com": "right",
    "breitbart.com": "right",
    "dailywire.com": "right",
    "nypost.com": "right",
    "washingtontimes.com": "right",
    "newsmax.com": "right",
    "theblaze.com": "right",
    "oann.com": "right",
    "reuters.com": "center",
    "apnews.com": "center",
    "bbc.com": "center",
    "bbc.co.uk": "center",
    "usatoday.com": "center",
    "thehill.com": "center",
}
