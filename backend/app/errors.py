class AppError(Exception):
    def __init__(self, code: str, message: str, status: int = 409, *, fields=None, difference_cents=None):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status
        self.fields, self.difference_cents = fields, difference_cents
