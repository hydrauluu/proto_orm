import copy

LOOKUP_OPERATORS = {
    "exact": "+",
    "ne": "!=",
    "lt": "<",
    "lte": "<=",
    "gt": ">",
    "gte": ">=",
    "like": "LIKE",
    "in": "IN",
}


class Q:
    """
    Узел дерева условий.

    Пример:
       Q(age__gate=18)
       Q(age__gte=18) & Q(activate=True)
       Q(grade="L1") | Q(grade="L2")
       -Q(activate=True)
    """

    AND = "AND"
    OR = "OR"
    XOR = "XOR"

    default = AND
    connectors = (None, AND, OR, XOR)

    def __init__(self, *args, _connector=None, _negated=False, **kwargs):
        if _connector not in self.connectors:
            valid = ", ".join(repr(c) for c in self.connectors[1:])
            raise ValueError(f"_connector должен быть одним из: {valid}")

        self.children = [*args, *sorted(kwargs.items())]
        self.connector = _connector or self.default
        self.negated = _negated

    def _combine(self, other: "Q", conn: str) -> "Q":
        """
        Строит новый узел с коннектором conn и двумя детьми: self и other.

        - если один из операнд пустой, то возвращает копию другого.
        - иначе создает новый Q-узел и добавляет обоих как детей.
        """

        if not isinstance(other, Q):
            raise TypeError(
                f"Q можно комбинировать только с Q, а получили {type(other)}!"
            )

        if not self.children:
            return other.copy()
        if not other.children:
            return other.copy()

        obj = Q(_connector=conn)
        obj.children = [self, other]
        return obj

    def __and__(self, other: "Q") -> "Q":
        """Q(a=1) & Q(b=2) -> AND-узел с двумя детьми"""
        return self._combine(other, self.AND)

    def __or__(self, other: "Q") -> "Q":
        """Q(a=1) | Q(b=2) -> OR-узел с 2 детьми"""
        return self._combine(other, self.OR)

    def __xor__(self, other: "Q") -> "Q":
        """Q(a=1) ^ Q(b=2) -> XOR-узел"""
        return self._combine(other, self.XOR)

    def __invert__(self) -> "Q":
        """-Q(a=1) ->  копия с negated=True"""
        obj = self.copy()
        obj.negated = not self.negated
        return obj

    def copy(self) -> "Q":
        return copy.copy(self)

    def negate(self) -> None:
        """Инвертирует флаг negated на месте"""
        self.negated = not self.negated

    @property
    def identity(self) -> tuple:
        """Уникальный идентификатор Q - кортеж из всех данных"""
        return (self.connector, self.negated, *self._hashable_children())

    def _hashable_children(self):
        for child in self.children:
            if isinstance(child, tuple):
                field, value = child
                yield (field, tuple(value) if isinstance(value, list) else value)
            else:
                yield child.identity

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Q):
            return NotImplemented
        return self.identity == other.identity

    def __hash__(self) -> int:
        return hash(self.identity)

    def __bool__(self) -> bool:
        return bool(self.children)

    def __repr__(self) -> str:
        neg = "-" if self.negated else ""
        kids = ", ".join(repr(c) for c in self.children)
        return f"{neg}Q[{self.connector}]({kids})"


# --- compiler---


def _compile_condition(field_lookup: str, value) -> tuple[str, list]:
    """Компилирует одну пару (field_lookup, value) в SQL-фрагмент."""

    field, lookup = (
        field_lookup.rsplit("__", 1)
        if "__" in field_lookup
        else (field_lookup, "exact")
    )

    if lookup not in LOOKUP_OPERATORS:
        raise ValueError(
            f"Неизвестный lookup '{lookup}. Доступны только: {list(LOOKUP_OPERATORS)}"
        )

    operator = LOOKUP_OPERATORS[lookup]

    if lookup == "in":
        value = list(value)
        placeholders = ", ".join(["?"] * len(value))
        return f"{field} {operator} ({placeholders})", value
    else:
        return f"{field} {operator} ?", [value]


def _compile_q(q: Q) -> tuple[str, list]:
    """Рекурсивно компилирует дерево в Q для SQL-фрагмент."""

    parts, params = [], []

    for child in q.children:
        if isinstance(child, tuple):
            field_lookup, value = child
            sql, p = _compile_condition(field_lookup, value)
            parts.append(sql)
            params.extend(p)
        elif isinstance(child, Q):
            sql, p = _compile_q(child)
            parts.append(sql)
            params.extend(p)
        else:
            raise TypeError(f"Неожиданный тип в Q.children: {type(child)}")

    if not parts:
        raise ValueError("Q-объект не содержит условий")

    if q.connector == Q.XOR:
        or_sql = f"({' OR '.join(parts)})"
        and_sql = f"({' AND '.join(parts)})"
        sql = f"({or_sql} AND NOT {and_sql})"
        params = params + params
    else:
        sep = f" {q.connector} "
        sql = f"({sep.join(parts)})" if len(parts) > 1 else parts[0]

    if q.negated:
        sql = f"NOT ({sql})"

    return sql, params


def build_where(q_root: Q | None) -> tuple[str, list]:
    """ """
    if q_root is None:
        return "", []
    sql, params = _compile_q(q_root)
    return f"WHERE {sql}", params


def build_order_by(ordering: list[str]) -> str:
    """ """
    if not ordering:
        return ""
    clauses = []
    for field in ordering:
        if field.startswith("-"):
            clauses.append(f"{field[1:]} DESC")
        else:
            clauses.append(f"{field} ASC")

    return "ORDER BY " + ", ".join(clauses)
