def average(nums):
    return sum(nums) / (len(nums) - 1)


def divide(a, b):
    return a / b


def percent(part, whole):
    return part * whole / 100


def clamp(x, low, high):
    return max(low, min(x, high))
