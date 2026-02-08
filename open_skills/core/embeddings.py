"""Provider-agnostic embeddings generation."""

import httpx

PROVIDERS = {
    "openai": {
        "url": "https://api.openai.com/v1/embeddings",
        "default_model": "text-embedding-3-large",
        "default_dimensions": 1536,
    },
    "mistral": {
        "url": "https://api.mistral.ai/v1/embeddings",
        "default_model": "mistral-embed",
        "default_dimensions": 1024,
    },
}


async def generate_embedding(
    text: str,
    provider: str,
    api_key: str,
    model: str | None = None,
) -> list[float]:
    """Generate embedding using the specified provider.

    Args:
        text: Text to embed
        provider: Provider name (e.g., "openai", "mistral")
        api_key: API key for the provider
        model: Model name (uses provider default if not set)

    Returns:
        List of floats representing the embedding vector

    Raises:
        ValueError: If provider is not supported
        httpx.HTTPError: If API request fails
    """
    if provider not in PROVIDERS:
        raise ValueError(f"Unsupported provider: {provider}. Supported: {list(PROVIDERS.keys())}")

    provider_config = PROVIDERS[provider]
    model = model or provider_config["default_model"]

    async with httpx.AsyncClient() as client:
        response = await client.post(
            provider_config["url"],
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"input": text, "model": model},
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        return data["data"][0]["embedding"]
