MAX_CENTS = 9_999_999_999


def installments(total: int, count: int) -> list[int]:
    if not 1 <= count <= 120 or not count <= total <= MAX_CENTS:
        raise ValueError("Valor ou quantidade de parcelas inválidos.")
    quotient, remainder = divmod(total, count)
    return [quotient + (i < remainder) for i in range(count)]


def allocate(total: int, weights: list[int]) -> list[int]:
    if total < 0 or not weights or any(w < 0 for w in weights) or sum(weights) <= 0:
        raise ValueError("Divisão inválida.")
    denominator = sum(weights)
    result = [total * w // denominator for w in weights]
    remainder = total - sum(result)
    eligible = [i for i, w in enumerate(weights) if w > 0]
    for i in eligible[:remainder]:
        result[i] += 1
    return result
