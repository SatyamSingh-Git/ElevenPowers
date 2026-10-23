class MarkliteError(ValueError):
    """Input or options marklite refuses. `line` is 1-based, or None when no line applies."""

    def __init__(self, message, line=None):
        super().__init__(message)
        self.message = message
        self.line = line

    def __str__(self):
        return self.message if self.line is None else f"line {self.line}: {self.message}"
