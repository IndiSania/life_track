"""Exception khusus aplikasi."""


class AppError(Exception):
    """Base error aplikasi."""


class ValidationError(AppError):
    """Input tidak valid."""


class NotFoundError(AppError):
    """Data yang dicari tidak ada."""
