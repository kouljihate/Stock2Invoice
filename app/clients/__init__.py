"""Client adapters: same class/method surface as the monolith's models and
services, implemented over the domain services' internal REST APIs."""

from .http import ApiError  # noqa: F401  (routes catch this by name)

__all__ = ['ApiError']
