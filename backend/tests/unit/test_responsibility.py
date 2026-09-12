"""EDIT-01: exact responsibility distribution across open obligations."""

import pytest

from app.domain.money import MAX_CENTS
from app.domain.responsibility import allocate_aggregate_split, responsibility_preview_hash


def totals(matrix):
    rows = [sum(weight for _, weight in row) for row in matrix]
    columns = {}
    for row in matrix:
        for user_id, weight in row:
            columns[user_id] = columns.get(user_id, 0) + weight
    return rows, columns


def test_even_split_is_preserved_on_every_obligation():
    result = allocate_aggregate_split([100, 100], [("douglas", 100), ("vanessa", 100)])
    assert result == [
        [("douglas", 50), ("vanessa", 50)],
        [("douglas", 50), ("vanessa", 50)],
    ]


def test_indivisible_cents_keep_exact_row_and_column_totals():
    result = allocate_aggregate_split([1, 1], [("douglas", 1), ("vanessa", 1)])
    assert result == [[("douglas", 1)], [("vanessa", 1)]]
    assert totals(result) == ([1, 1], {"douglas": 1, "vanessa": 1})


def test_uneven_obligations_and_shares_keep_both_margins_exact():
    result = allocate_aggregate_split(
        [34, 33, 33], [("douglas", 67), ("vanessa", 22), ("bia", 11)]
    )
    assert totals(result) == (
        [34, 33, 33],
        {"douglas": 67, "vanessa": 22, "bia": 11},
    )


def test_zero_aggregate_share_is_not_emitted_as_snapshot():
    result = allocate_aggregate_split([40, 60], [("douglas", 0), ("vanessa", 100)])
    assert result == [[("vanessa", 40)], [("vanessa", 60)]]


def test_full_transfer_emits_only_destination():
    result = allocate_aggregate_split([51, 50], [("douglas", 0), ("vanessa", 101)])
    assert result == [[("vanessa", 51)], [("vanessa", 50)]]


def test_result_is_deterministic_for_same_ordered_input():
    arguments = ([17, 19, 23], [("a", 20), ("b", 20), ("c", 19)])
    assert allocate_aggregate_split(*arguments) == allocate_aggregate_split(*arguments)


def test_maximum_supported_total_is_distributed_exactly():
    result = allocate_aggregate_split(
        [MAX_CENTS - 1, 1], [("douglas", MAX_CENTS // 2), ("vanessa", MAX_CENTS - MAX_CENTS // 2)]
    )
    assert totals(result) == (
        [MAX_CENTS - 1, 1],
        {"douglas": MAX_CENTS // 2, "vanessa": MAX_CENTS - MAX_CENTS // 2},
    )


@pytest.mark.parametrize("obligations", [[], [0], [-1], [MAX_CENTS + 1]])
def test_invalid_obligations_are_rejected(obligations):
    with pytest.raises(ValueError, match="Obrigações inválidas"):
        allocate_aggregate_split(obligations, [("douglas", sum(obligations))])


@pytest.mark.parametrize(
    "shares",
    [[], [("douglas", -1)], [("douglas", 1), ("douglas", 1)], [("", 1)]],
)
def test_invalid_shares_are_rejected(shares):
    with pytest.raises(ValueError, match="Divisão inválida"):
        allocate_aggregate_split([2], shares)


def test_share_total_must_equal_obligation_total():
    with pytest.raises(ValueError, match="total das responsabilidades"):
        allocate_aggregate_split([100], [("douglas", 99)])


def test_inputs_are_not_mutated():
    obligations = [50, 50]
    shares = [("douglas", 25), ("vanessa", 75)]
    allocate_aggregate_split(obligations, shares)
    assert obligations == [50, 50]
    assert shares == [("douglas", 25), ("vanessa", 75)]


def test_preview_hash_is_canonical_and_sensitive_to_the_read_set():
    first = {
        "source_version": 3,
        "installments": [{"id": "i1", "version": 2, "amount_cents": 100}],
        "shares": [{"user_id": "vanessa", "weight": 100}],
    }
    reordered = {
        "shares": [{"weight": 100, "user_id": "vanessa"}],
        "installments": [{"amount_cents": 100, "version": 2, "id": "i1"}],
        "source_version": 3,
    }
    changed = {**first, "source_version": 4}

    assert responsibility_preview_hash(first) == responsibility_preview_hash(reordered)
    assert responsibility_preview_hash(first) != responsibility_preview_hash(changed)
    assert len(responsibility_preview_hash(first)) == 64
