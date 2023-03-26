class FrankEnergieException(Exception):
    """Base exception."""


class AuthRequiredException(FrankEnergieException):
    """Authentication required for this request."""


class AuthException(FrankEnergieException):
    """Authentication/login failed."""
