"""BUY-01 AC04, SPLIT-01, ADV-01 AC06."""

import pytest
from app.domain.money import installments, allocate


def test_installment_rounding():
    assert installments(10000, 3) == [3334, 3333, 3333]
    assert installments(30000, 3) == [10000, 10000, 10000]


def test_responsibility_rounding():
    assert allocate(3333, [1, 1]) == [1667, 1666]
    assert allocate(10000, [0, 1]) == [0, 10000]
    assert allocate(10000, [1, 1]) == [5000, 5000]
    assert allocate(19999, [10000, 10000]) == [10000, 9999]
    assert allocate(19998, [10000, 10000]) == [9999, 9999]


@pytest.mark.parametrize(
    "amount,count", [(0, 1), (-1, 2), (1, 2), (100, 0), (1000, 121), (10000000000, 1)]
)
def test_invalid_installments(amount, count):
    with pytest.raises(ValueError):
        installments(amount, count)
