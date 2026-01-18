"""
TTS Factory - Factory for creating TTS service instances.

This module implements the Factory pattern for TTS services,
following the Open/Closed Principle (OCP) from SOLID.
New TTS providers can be added without modifying existing code.
"""

from typing import Optional

from app.services.base_tts_service import BaseTTSService
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Registry of available TTS providers
_TTS_PROVIDERS = {}


def register_tts_provider(name: str, factory_func):
    """
    Register a TTS provider factory function.

    This allows for dynamic registration of new providers
    without modifying the factory code (OCP).
    """
    _TTS_PROVIDERS[name] = factory_func


def get_tts_service(provider: Optional[str] = None) -> BaseTTSService:
    """
    Get a TTS service instance by provider name.

    Args:
        provider: The TTS provider name ("edge_tts" or "chatterbox").
                  If None, uses the default from settings.

    Returns:
        A TTS service instance implementing BaseTTSService.

    Raises:
        ValueError: If the provider is not supported.
    """
    # Use default if not specified
    provider = provider or settings.default_tts_provider

    logger.debug("Getting TTS service", provider=provider)

    # Lazy import to avoid circular dependencies and startup overhead
    if provider == "chatterbox":
        from app.services.chatterbox_tts_service import ChatterboxTTSService

        return ChatterboxTTSService()
    elif provider == "edge_tts":
        from app.services.tts_service import EdgeTTSService

        return EdgeTTSService()
    else:
        # Check registry for custom providers
        if provider in _TTS_PROVIDERS:
            return _TTS_PROVIDERS[provider]()

        logger.warning(
            "Unknown TTS provider, falling back to edge_tts", requested=provider
        )
        from app.services.tts_service import EdgeTTSService

        return EdgeTTSService()


def get_available_providers() -> list[str]:
    """Get list of available TTS provider names."""
    return ["edge_tts", "chatterbox"] + list(_TTS_PROVIDERS.keys())


# Convenience function for getting the default service
def get_default_tts_service() -> BaseTTSService:
    """Get the default TTS service based on settings."""
    return get_tts_service(settings.default_tts_provider)
