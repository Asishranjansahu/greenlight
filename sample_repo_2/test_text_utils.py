from text_utils import is_palindrome, slugify, truncate, word_count


def test_slugify_basic():
    assert slugify("Hello, World!") == "hello-world"


def test_slugify_collapses_spaces():
    assert slugify("  Multiple   spaces here ") == "multiple-spaces-here"


def test_truncate_short_text_unchanged():
    assert truncate("hello", 10) == "hello"


def test_truncate_respects_width():
    result = truncate("The quick brown fox", 10)
    assert result == "The qui..."
    assert len(result) == 10


def test_word_count_simple():
    assert word_count("one two three") == 3


def test_word_count_extra_whitespace():
    assert word_count("  one   two \n three ") == 3


def test_palindrome_simple():
    assert is_palindrome("level")


def test_palindrome_ignores_case_and_punctuation():
    assert is_palindrome("A man, a plan, a canal: Panama")
