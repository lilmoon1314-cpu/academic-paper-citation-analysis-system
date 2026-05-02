import re
from collections import Counter

STOPWORDS = set([
    "the", "and", "for", "using", "based", "with", "from", "that", "this", "which",
    "into", "learning", "model", "neural", "network", "deep", "towards", "data",
    "system", "approach", "method", "via", "analysis", "application", "new", "an",
    "on", "of", "in", "to", "by", "as", "is", "a", "its", "are", "we", "our", "it", "not",
    "their", "also", "or", "can", "has", "been", "but", "more", "some", "than", "all",
    "two", "single", "large", "small", "high", "low", "one", "first", "results",
    "paper", "study", "survey", "review", "research", "work", "case", "based", "end",
    "over", "under", "between", "about", "through", "during", "after", "before",
    "multi", "cross", "semi", "self", "non", "pre", "post", "re", "co", "sub", "super",
])


def clean_search_keyword(keyword):
    cleaned = re.sub(r'[()\[\]{}"\'*?:\\^~]', ' ', keyword)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def extract_keywords(titles, top_n=3):
    unigrams = []
    bigrams = []
    for title in titles:
        tokens = re.sub(r"[^a-zA-Z0-9\s\-]", " ", title.lower()).split()
        tokens = [t.strip("-") for t in tokens if len(t) > 2 and t not in STOPWORDS]
        unigrams.extend(tokens)
        for i in range(len(tokens) - 1):
            bigrams.append(f"{tokens[i]} {tokens[i + 1]}")

    bigram_counter = Counter(bigrams)
    unigram_counter = Counter(unigrams)

    selected = []
    used_words = set()

    for phrase, cnt in bigram_counter.most_common(20):
        if cnt < 3:
            break
        words = phrase.split()
        if not any(w in used_words for w in words):
            selected.append(phrase.title())
            used_words.update(words)
        if len(selected) >= top_n:
            break

    if len(selected) < top_n:
        for word, _ in unigram_counter.most_common(20):
            if word not in used_words:
                selected.append(word.capitalize())
                used_words.add(word)
            if len(selected) >= top_n:
                break

    return " · ".join(selected) if selected else None
