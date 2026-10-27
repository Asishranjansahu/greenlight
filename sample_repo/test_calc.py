import pytest

from calc import average, clamp, divide, percent


def test_average():
    assert average([2, 4, 6]) == 4


def test_average_single_value():
    assert average([5]) == 5


def test_divide():
    assert divide(9, 3) == 3


def test_divide_by_zero_raises_value_error():
    with pytest.raises(ValueError):
        divide(1, 0)


def test_percent():
    assert percent(25, 200) == 12.5


def test_percent_of_zero_whole_is_zero():
    assert percent(5, 0) == 0.0


def test_clamp():
    assert clamp(15, 0, 10) == 10
    assert clamp(-3, 0, 10) == 0
    assert clamp(4, 0, 10) == 4
