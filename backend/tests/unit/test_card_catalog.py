import pytest

from app.domain.card_catalog import (
    CARD_INSTITUTIONS,
    CARD_NETWORKS,
    normalize_institution,
    normalize_network,
)


def test_catalog_has_the_sixteen_approved_stable_keys_including_neon():
    assert tuple(item.key for item in CARD_INSTITUTIONS) == (
        "nubank", "itau", "bradesco", "santander", "bb", "caixa", "inter", "c6",
        "btg", "xp", "picpay", "mercado_pago", "neon", "sicoob", "sicredi", "other",
    )
    assert next(item.label for item in CARD_INSTITUTIONS if item.key == "neon") == "Neon"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("Nubank", "nubank"), ("Itaú", "itau"), ("Banco do Brasil", "bb"),
     ("Mercado Pago", "mercado_pago"), ("Banco Neon", "neon"), ("desconhecido", "other")],
)
def test_institution_aliases_are_normalized_without_changing_the_catalog(raw, expected):
    assert normalize_institution(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [(None, None), ("Visa", "visa"), ("master card", "mastercard"),
     ("American Express", "amex"), ("Hipercard", "hipercard")],
)
def test_network_aliases_are_normalized(raw, expected):
    assert normalize_network(raw) == expected


def test_network_catalog_is_bounded_and_rejects_unknown_values():
    assert tuple(item.key for item in CARD_NETWORKS) == (
        "visa", "mastercard", "elo", "amex", "hipercard", "other",
    )
    with pytest.raises(ValueError, match="Bandeira não reconhecida"):
        normalize_network("inventada")
