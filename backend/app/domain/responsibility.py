from collections.abc import Sequence

from app.domain.money import MAX_CENTS, allocate


def allocate_aggregate_split(
    obligations: Sequence[int], shares: Sequence[tuple[str, int]]
) -> list[list[tuple[str, int]]]:
    """Distribute aggregate user totals into exact per-obligation snapshots."""
    if not obligations or any(amount <= 0 or amount > MAX_CENTS for amount in obligations):
        raise ValueError("Obrigações inválidas.")
    user_ids = [user_id for user_id, _ in shares]
    if (
        not shares
        or any(not user_id or weight < 0 for user_id, weight in shares)
        or len(set(user_ids)) != len(user_ids)
    ):
        raise ValueError("Divisão inválida.")
    if sum(obligations) != sum(weight for _, weight in shares):
        raise ValueError("O total das responsabilidades deve fechar com as obrigações.")

    remaining = [weight for _, weight in shares]
    matrix: list[list[tuple[str, int]]] = []
    for amount in obligations:
        allocated = allocate(amount, remaining)
        matrix.append(
            [
                (user_id, weight)
                for (user_id, _), weight in zip(shares, allocated, strict=True)
                if weight > 0
            ]
        )
        remaining = [
            weight - assigned
            for weight, assigned in zip(remaining, allocated, strict=True)
        ]
    return matrix
