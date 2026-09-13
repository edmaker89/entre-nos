from dataclasses import dataclass
import unicodedata


@dataclass(frozen=True)
class CatalogItem:
    key: str
    label: str
    aliases: tuple[str, ...] = ()


CARD_INSTITUTIONS = (
    CatalogItem("nubank", "Nubank", ("nu",)),
    CatalogItem("itau", "Itaú", ("itau unibanco",)),
    CatalogItem("bradesco", "Bradesco"),
    CatalogItem("santander", "Santander"),
    CatalogItem("bb", "Banco do Brasil", ("bb",)),
    CatalogItem("caixa", "Caixa", ("caixa economica federal",)),
    CatalogItem("inter", "Inter", ("banco inter",)),
    CatalogItem("c6", "C6 Bank", ("c6",)),
    CatalogItem("btg", "BTG Pactual", ("btg",)),
    CatalogItem("xp", "XP", ("xp investimentos",)),
    CatalogItem("picpay", "PicPay"),
    CatalogItem("mercado_pago", "Mercado Pago"),
    CatalogItem("neon", "Neon", ("banco neon",)),
    CatalogItem("sicoob", "Sicoob"),
    CatalogItem("sicredi", "Sicredi"),
    CatalogItem("other", "Outra instituição", ("outra", "outro")),
)

CARD_NETWORKS = (
    CatalogItem("visa", "Visa"),
    CatalogItem("mastercard", "Mastercard", ("master card",)),
    CatalogItem("elo", "Elo"),
    CatalogItem("amex", "American Express", ("american express",)),
    CatalogItem("hipercard", "Hipercard"),
    CatalogItem("other", "Outra"),
)


def _search_key(value: str) -> str:
    plain = "".join(
        character
        for character in unicodedata.normalize("NFKD", value.casefold())
        if not unicodedata.combining(character)
    )
    return " ".join(plain.replace("_", " ").split())


def _aliases(items: tuple[CatalogItem, ...]) -> dict[str, str]:
    return {
        _search_key(alias): item.key
        for item in items
        for alias in (item.key, item.label, *item.aliases)
    }


_INSTITUTION_ALIASES = _aliases(CARD_INSTITUTIONS)
_NETWORK_ALIASES = _aliases(CARD_NETWORKS)


def normalize_institution(value: str) -> str:
    return _INSTITUTION_ALIASES.get(_search_key(value), "other")


def normalize_network(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    try:
        return _NETWORK_ALIASES[_search_key(value)]
    except KeyError as exc:
        raise ValueError("Bandeira não reconhecida.") from exc


def institution_label(key: str) -> str:
    try:
        return next(item.label for item in CARD_INSTITUTIONS if item.key == key)
    except StopIteration as exc:
        raise ValueError("Instituição não reconhecida.") from exc


def serialize_catalog(items: tuple[CatalogItem, ...]) -> list[dict[str, object]]:
    return [
        {"key": item.key, "label": item.label, "aliases": list(item.aliases)} for item in items
    ]
