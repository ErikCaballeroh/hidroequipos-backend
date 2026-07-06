class InvalidDateRangeError(Exception):
    def __init__(self) -> None:
        super().__init__("Start date cannot be later than end date")
