import os
from urllib.parse import urlparse


def get_env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:1234/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "local-model")
OPENSEARCH_URL = os.getenv("OPENSEARCH_URL", "http://localhost:9200")
OPENSEARCH_VERIFY_CERTS = get_env_bool("OPENSEARCH_VERIFY_CERTS", False)
OPENSEARCH_USERNAME = os.getenv("OPENSEARCH_USERNAME")
OPENSEARCH_PASSWORD = os.getenv("OPENSEARCH_PASSWORD")
DEFAULT_INDEX_NAME = os.getenv("DEFAULT_INDEX_NAME", "pdf-rag")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")


def get_opensearch_client_config() -> dict:
    parsed = urlparse(OPENSEARCH_URL)
    if not parsed.scheme or not parsed.hostname:
        raise ValueError(
            "OPENSEARCH_URL must include a scheme and hostname, for example "
            "'http://localhost:9200'."
        )

    use_ssl = parsed.scheme == "https"
    config = {
        "hosts": [
            {
                "host": parsed.hostname,
                "port": parsed.port or (443 if use_ssl else 80),
                "scheme": parsed.scheme,
            }
        ],
        "http_compress": True,
        "use_ssl": use_ssl,
        "verify_certs": OPENSEARCH_VERIFY_CERTS,
    }

    if OPENSEARCH_USERNAME or OPENSEARCH_PASSWORD:
        config["http_auth"] = (OPENSEARCH_USERNAME or "", OPENSEARCH_PASSWORD or "")

    return config
