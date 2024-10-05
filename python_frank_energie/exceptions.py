"""Exceptions for the Frank Energie API."""

class FrankEnergieException(Exception):
    """Base exception."""

class AuthRequiredException(FrankEnergieException):
    """Authentication required for this request."""

class AuthException(FrankEnergieException):
    """Authentication/login failed."""

class RequestException(FrankEnergieException):
    """Request failed."""

class NoSuitableSitesFoundError(FrankEnergieError):
    """Request failed."""

class FrankEnergieError(Exception):
    """Base class for all FrankEnergie-related errors."""

class LoginError(FrankEnergieError):
    """Raised when login to FrankEnergie fails."""

class NetworkError(FrankEnergieError):
    """Raised for network-related errors in FrankEnergie."""

class SmartTradingNotEnabledException(FrankEnergieError):
    """Exception raised when smart trading is not enabled for the user."""

class ConnectionException(FrankEnergieError):
    """Raised for network-related errors in FrankEnergie."""
