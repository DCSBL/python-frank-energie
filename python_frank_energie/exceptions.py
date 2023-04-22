"""Exceptions for the Frank Energie API."""


class FrankEnergieException(Exception):
    """Base exception."""


class AuthRequiredException(FrankEnergieException):
    """Authentication required for this request."""


class AuthException(FrankEnergieException):
    """Authentication/login failed."""


class RequestException(FrankEnergieException):
    """Request failed."""
