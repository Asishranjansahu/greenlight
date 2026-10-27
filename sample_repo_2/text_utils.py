import re

from config import ELLIPSIS, SEPARATOR


def slugify(text):
    words = re.findall(r"[a-z0-9]+", text.lower())
    return SEPARATOR.join(words)


def truncate(text, width):
    if len(text) <= width:
        return text
    return text[:width] + ELLIPSIS


def word_count(text):
    return len(text.split(" "))


def is_palindrome(text):
    return text == text[::-1]
