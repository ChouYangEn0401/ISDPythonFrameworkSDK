"""The high-level loader: read a credential, and transparently decrypt it.

:class:`CredentialVault` ties the :mod:`.sources` waterfall together with
:mod:`cipher_kit`: if a looked-up value is a ``CK1`` sealed token *and* you
supplied key material, it is unsealed automatically.  Plain values pass through
untouched — and reading plain values never imports ``cryptography``.
"""
from __future__ import annotations

from .sources import (
    MISSING,
    ChainSource,
    ConfigSource,
    DotEnvSource,
    JsonSource,
    OsEnvSource,
    YamlSource,
)

__all__ = ["CredentialVault", "load_secret"]

# Distinct from None so callers can use default=None meaningfully.
_NO_DEFAULT = object()

# Cheap, dependency-free prefix used to decide whether to even look at cipher_kit.
_TOKEN_PREFIX = "CK1."


def _build_source(spec, *, search_from=None) -> ConfigSource:
    """Turn a string spec or a ConfigSource into a ConfigSource."""
    if isinstance(spec, ConfigSource):
        return spec
    if spec == "os_env":
        return OsEnvSource()
    text = str(spec)
    low = text.lower()
    if text == ".env":  # bare string → auto-discover the nearest .env
        return DotEnvSource(None, search_from=search_from)
    if low.endswith(".env"):  # an explicit path to a .env file
        return DotEnvSource(text, search_from=search_from)
    if low.endswith((".yaml", ".yml")):
        return YamlSource(text)
    if low.endswith(".json"):
        return JsonSource(text)
    raise ValueError(
        f"Unrecognised source spec: {spec!r}. Use 'os_env', a path ending in "
        f".env/.yaml/.yml/.json, or a ConfigSource instance."
    )


class CredentialVault:
    """Load credentials from one or more sources, decrypting sealed values.

    Parameters
    ----------
    sources:
        Ordered list of source specs (a waterfall — first hit wins).  Each item
        is either ``"os_env"``, a path (``".env"`` / ``"config.yaml"`` /
        ``"secrets.json"``), or a :class:`ConfigSource` instance.  Defaults to
        ``["os_env", ".env"]`` (environment overrides the dotenv file).
    search_from:
        Directory to start ``.env`` auto-discovery from (defaults to cwd).

    Examples
    --------
        vault = CredentialVault(["os_env", ".env", "secrets.yaml"])
        url   = vault.get("DATABASE_URL")                       # plain value
        token = vault.get("API_KEY", password="my-passphrase")  # auto-unsealed
    """

    def __init__(self, sources=None, *, search_from=None):
        if sources is None:
            sources = ["os_env", ".env"]
        self._chain = ChainSource(
            [_build_source(s, search_from=search_from) for s in sources]
        )

    def get(
        self,
        key: str,
        *,
        default=_NO_DEFAULT,
        password: str | None = None,
        key_source=None,
        private_key=None,
        prompt_password: bool = False,
        decrypt: bool = True,
        required: bool = True,
        encoding: str = "utf-8",
    ):
        """Return the value for *key*, transparently unsealing ``CK1`` tokens.

        Decryption happens only when ``decrypt`` is true, the value looks like a
        token, and key material is available.  Otherwise the raw value is
        returned untouched.

        Key material can be:

        * ``password=`` / ``key_source=`` — passphrase-based symmetric tokens;
        * ``private_key=`` — RSA-hybrid tokens;
        * ``prompt_password=True`` — a one-liner for "ask me the passphrase at
          runtime and never store it".  When set (and no explicit ``password`` /
          ``key_source`` / ``private_key`` is given), the passphrase is read via
          ``getpass`` only if the stored value is actually a sealed token.  Plain
          values are returned without ever prompting.

        Raises :class:`KeyError` when the key is absent and ``required`` is true
        with no ``default`` supplied.
        """
        value = self._chain.get(key)
        if value is MISSING:
            if default is not _NO_DEFAULT:
                return default
            if required:
                raise KeyError(
                    f"Credential {key!r} not found in any configured source."
                )
            return None

        has_key_material = (
            password is not None
            or key_source is not None
            or private_key is not None
            or prompt_password
        )
        if (
            decrypt
            and isinstance(value, str)
            and value.startswith(_TOKEN_PREFIX)
            and has_key_material
        ):
            # Cross-module bridge, routed through interop so a partial install
            # (credential_vault without cipher_kit) fails with the SDK's
            # standard "pip install ...[cipher_kit]" message. Lazy: only when we
            # actually need to decrypt a token.
            from ..interop import require_feature

            cipher_kit = require_feature("cipher_kit")

            # Sugar: prompt for the passphrase at runtime (getpass, never
            # stored) when asked and no explicit key material was supplied.
            if (
                prompt_password
                and password is None
                and key_source is None
                and private_key is None
            ):
                key_source = cipher_kit.PromptSecret()

            return cipher_kit.unseal(
                value,
                password=password,
                key_source=key_source,
                private_key=private_key,
                encoding=encoding,
            )
        return value

    def get_secret(self, key: str, **kwargs):
        """Like :meth:`get`, but *requires* the value to be a sealed token.

        Use this when a value must always be encrypted at rest — it raises if
        the stored value is plaintext, catching accidental unencrypted secrets.
        """
        kwargs.setdefault("required", True)
        value = self._chain.get(key)
        if value is MISSING:
            return self.get(key, **kwargs)  # delegate for default/required handling
        if isinstance(value, str) and not value.startswith(_TOKEN_PREFIX):
            raise ValueError(
                f"Credential {key!r} is stored in plaintext but get_secret() "
                f"requires a sealed token. Seal it with cipher_kit.seal(...)."
            )
        return self.get(key, **kwargs)

    def keys(self):
        """List all keys visible across the configured sources."""
        return sorted(self._chain.as_dict().keys())


def load_secret(
    key: str,
    *,
    env_path=None,
    search_from=None,
    password: str | None = None,
    key_source=None,
    private_key=None,
    prompt_password: bool = False,
    default=_NO_DEFAULT,
    required: bool = True,
    decrypt: bool = True,
    encoding: str = "utf-8",
):
    """One-shot convenience: read *key* from ``os.environ`` then a ``.env`` file.

    Equivalent to building a :class:`CredentialVault` over
    ``["os_env", env_path or ".env"]`` and calling :meth:`~CredentialVault.get`.
    Pass ``password=`` / ``key_source=`` / ``private_key=`` to auto-unseal a
    sealed value, or ``prompt_password=True`` to be asked for the passphrase at
    runtime (via ``getpass``, never stored)::

        api_key = load_secret("ENC_API_KEY", env_path="chatgpt_local.env",
                              prompt_password=True)
    """
    vault = CredentialVault(
        sources=["os_env", env_path if env_path else ".env"], search_from=search_from
    )
    return vault.get(
        key,
        default=default,
        password=password,
        key_source=key_source,
        private_key=private_key,
        prompt_password=prompt_password,
        decrypt=decrypt,
        required=required,
        encoding=encoding,
    )
