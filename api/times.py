from datetime import datetime, timedelta, timezone


def utc_now():
    return datetime.now(timezone.utc)


def utc_now_float():
    return utc_now().timestamp()


def utc_now_int():
    return int(utc_now_float())


def time_ago(**kwargs):
    return utc_now() - timedelta(**kwargs)


def time_ago_float(**kwargs):
    return time_ago(**kwargs).timestamp()


def time_in_the_future(**kwargs):
    return utc_now() + timedelta(**kwargs)


def time_in_the_future_float(**kwargs):
    return time_in_the_future(**kwargs).timestamp()
