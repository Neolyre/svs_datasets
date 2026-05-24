"""Vocabulary helpers and conservative special-token normalization."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

# these special tokens are cross-vocabulary; for language-specific phone normalization, see preprocessing.phonesets
BLANK_TOKEN = "<BLANK>"
SP_TOKEN = "<SP>"
AP_TOKEN = "<AP>"
SPECIAL_TOKENS = (
    BLANK_TOKEN,
    SP_TOKEN,
    AP_TOKEN,
)

DEFAULT_SPECIAL_TOKEN_ALIASES: dict[str, tuple[str, ...]] = {
    BLANK_TOKEN: (
        BLANK_TOKEN,
        "<blank>",
        "blank",
        "_",
    ),
    SP_TOKEN: (
        SP_TOKEN,
        "SP",
        "sp",
        "sil",
        "SIL",
        "pau",
        "PAU",
        "silence",
        "<sil>",
    ),
    AP_TOKEN: (
        AP_TOKEN,
        "AP",
        "ap",
        "br",
        "BR",
        "breath",
        "BREATHE",
        "EP",
    ),
}


def _dedupe_tokens(tokens: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    unique_tokens: list[str] = []
    for token in tokens:
        if token not in seen:
            seen.add(token)
            unique_tokens.append(token)
    return tuple(unique_tokens)


def build_alias_map(extra_aliases: Mapping[str, str] | None = None) -> dict[str, str]:
    """Build the canonical token alias mapping."""
    alias_map: dict[str, str] = {}
    for canonical_token, aliases in DEFAULT_SPECIAL_TOKEN_ALIASES.items():
        for alias in aliases:
            alias_map[alias] = canonical_token

    if extra_aliases is not None:
        alias_map.update(dict(extra_aliases))

    return alias_map


def _build_lower_alias_map(alias_map: Mapping[str, str]) -> dict[str, str]:
    return {alias.lower(): canonical for alias, canonical in alias_map.items()}


DEFAULT_ALIAS_MAP = build_alias_map()
DEFAULT_LOWER_ALIAS_MAP = _build_lower_alias_map(DEFAULT_ALIAS_MAP)


def canonicalize_token(
    token: str,
    *,
    alias_map: Mapping[str, str] | None = None,
    lower_alias_map: Mapping[str, str] | None = None,
) -> str:
    """Normalize special-token aliases while preserving unknown phones."""
    if not isinstance(token, str):
        raise TypeError(f"token must be a string, got {type(token).__name__}")

    stripped = token.strip()
    if not stripped:
        raise ValueError("token must not be empty")

    exact_map = DEFAULT_ALIAS_MAP if alias_map is None else alias_map
    lower_map = DEFAULT_LOWER_ALIAS_MAP if lower_alias_map is None else lower_alias_map

    if stripped in exact_map:
        return exact_map[stripped]

    return lower_map.get(stripped.lower(), stripped)


def canonicalize_tokens(
    tokens: Iterable[str],
    *,
    alias_map: Mapping[str, str] | None = None,
    lower_alias_map: Mapping[str, str] | None = None,
) -> tuple[str, ...]:
    """Normalize a sequence of tokens into canonical special-token form."""
    return tuple(
        canonicalize_token(
            token,
            alias_map=alias_map,
            lower_alias_map=lower_alias_map,
        )
        for token in tokens
    )


def is_special_token(token: str) -> bool:
    """Return whether the token resolves to one of the canonical special tokens."""
    return canonicalize_token(token) in SPECIAL_TOKENS


@dataclass(frozen=True, slots=True)
class VocabularySpec:
    """Canonical vocabulary container with configurable aliases."""

    phone_tokens: tuple[str, ...] = ()
    extra_tokens: tuple[str, ...] = ()
    extra_aliases: dict[str, str] = field(default_factory=dict)
    _alias_map: dict[str, str] = field(init=False, repr=False)
    _lower_alias_map: dict[str, str] = field(init=False, repr=False)
    _tokens: tuple[str, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        alias_map = build_alias_map(self.extra_aliases)
        lower_alias_map = _build_lower_alias_map(alias_map)

        normalized_phone_tokens = canonicalize_tokens(
            self.phone_tokens,
            alias_map=alias_map,
            lower_alias_map=lower_alias_map,
        )
        normalized_extra_tokens = canonicalize_tokens(
            self.extra_tokens,
            alias_map=alias_map,
            lower_alias_map=lower_alias_map,
        )

        object.__setattr__(self, "_alias_map", alias_map)
        object.__setattr__(self, "_lower_alias_map", lower_alias_map)
        object.__setattr__(
            self,
            "_tokens",
            _dedupe_tokens(
                (
                    *SPECIAL_TOKENS,
                    *normalized_phone_tokens,
                    *normalized_extra_tokens,
                )
            ),
        )

    @property
    def tokens(self) -> tuple[str, ...]:
        """Return the vocabulary in deterministic ID order."""
        return self._tokens

    @property
    def token_to_id(self) -> dict[str, int]:
        """Return a token-to-ID mapping for the current vocabulary."""
        return {token: index for index, token in enumerate(self.tokens)}

    def canonicalize_token(self, token: str) -> str:
        """Normalize one token with the vocabulary's alias configuration."""
        return canonicalize_token(
            token,
            alias_map=self._alias_map,
            lower_alias_map=self._lower_alias_map,
        )

    def canonicalize_tokens(self, tokens: Iterable[str]) -> tuple[str, ...]:
        """Normalize a token sequence with the vocabulary's alias configuration."""
        return canonicalize_tokens(
            tokens,
            alias_map=self._alias_map,
            lower_alias_map=self._lower_alias_map,
        )


__all__ = [
    "AP_TOKEN",
    "BLANK_TOKEN",
    "DEFAULT_ALIAS_MAP",
    "DEFAULT_LOWER_ALIAS_MAP",
    "DEFAULT_SPECIAL_TOKEN_ALIASES",
    "SPECIAL_TOKENS",
    "SP_TOKEN",
    "VocabularySpec",
    "build_alias_map",
    "canonicalize_token",
    "canonicalize_tokens",
    "is_special_token",
]
