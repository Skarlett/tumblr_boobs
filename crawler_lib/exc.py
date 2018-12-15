class TooManyRequestsWarning(Warning):
    pass


class NoKeysInDatabase(ValueError):
    pass


class HourLimitCap(TooManyRequestsWarning):
    pass


class DayLimitCap(TooManyRequestsWarning):
    pass

class NoMorePosts(Exception):pass