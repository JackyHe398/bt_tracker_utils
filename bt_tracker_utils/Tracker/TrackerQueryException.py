class TrackerQueryException(Exception):
    default_message = "Tracker query error"
    def __init__(self, url = None, message=None):
        if url:
            message = f"{message or self.default_message} for '{url}'"
        else:
            message = message or self.default_message
        super().__init__(message or self.default_message)

class TimeoutError(TrackerQueryException):
    default_message = "Timeout Error:"
    def __init__(self, url = None, message=None):
        super().__init__(url, message or self.default_message)

class BadRequestError(TrackerQueryException):
    default_message = "Bad Request Error:"
    def __init__(self, url = None, message=None):
        super().__init__(url, message or self.default_message)

class InvalidResponseError(TrackerQueryException):
    default_message = "Invalid Response Error:"
    def __init__(self, url = None, message=None):
        super().__init__(url, message or self.default_message)

class UnexpectedError(TrackerQueryException):
    default_message = "Unexpected Error"
    def __init__(self, url=None, message=None, e=None):
        detail_message = f"{message or self.default_message}"
        if url:
            detail_message += f" for '{url}'"
        if e is not None:  # avoid falsy values
            detail_message += f" | Details: {repr(e)}"
        super().__init__(None, detail_message)
        self.original_exception = e