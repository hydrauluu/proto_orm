import copy


class Q:
    """
    Узел дерева условий.

    Примеры:
        Q(age__gte=18)
        Q(age__gte=18) & Q(active=True)
        Q(grade="L1") | Q(grade="L2")
        ~Q(active=True)
        Q(grade="L1") ^ Q(grade="L2")
    """

    AND = "AND"
    OR  = "OR"
    XOR = "XOR"

    default    = AND
    connectors = (None, AND, OR, XOR)

    def __init__(self, *args, _connector=None, _negated=False, **kwargs):
        if _connector not in self.connectors:
            valid = ", ".join(repr(c) for c in self.connectors[1:])
            raise ValueError(f"_connector должен быть одним из: {valid}")

        # Единый список детей как в Django:
        # args   — вложенные Q-объекты
        # kwargs — условия, превращаются в кортежи ("field__lookup", value)
        self.children  = [*args, *sorted(kwargs.items())]
        self.connector = _connector or self.default
        self.negated   = _negated

    def _combine(self, other: "Q", conn: str) -> "Q":
        """Строит новый узел с коннектором conn и двумя детьми: self и other.

        Если один операнд пустой — возвращает копию другого.
        """
        if not isinstance(other, Q):
            raise TypeError(f"Q можно комбинировать только с Q, получен {type(other)}")

        if not self.children:
            return other.copy()
        if not other.children:
            return self.copy()          # было other.copy() — баг

        obj = Q(_connector=conn)
        obj.children = [self, other]
        return obj

    def __and__(self, other: "Q") -> "Q":
        return self._combine(other, self.AND)

    def __or__(self, other: "Q") -> "Q":
        return self._combine(other, self.OR)

    def __xor__(self, other: "Q") -> "Q":
        return self._combine(other, self.XOR)

    def __invert__(self) -> "Q":
        obj = self.copy()
        obj.negated = not self.negated
        return obj

    def copy(self) -> "Q":
        return copy.copy(self)

    def negate(self) -> None:
        self.negated = not self.negated

    @property
    def identity(self) -> tuple:
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
        neg  = "~" if self.negated else ""
        kids = ", ".join(repr(c) for c in self.children)
        return f"{neg}Q[{self.connector}]({kids})"
