import copy
from warnings import resetwarnings

from Q import Q


LOOKUP_OPERATORS = {
    "exact": "=",
    "ne": "!=",
    "lt": "<",
    "lte": "<=",
    "gt": ">",
    "gte": ">=",
    "like": "LIKE",
    "in": "IN",
}


def _compile_condition(field_lookup: str, value) -> tuple[str, list]:
    """Компилирует одну пару (field_lookup, value) в SQL-фрагмент.

    "age__gte", 18        →  "age >= ?",        [18]
    "name", "Alice"       →  "name = ?",         ["Alice"]
    "id__in", [1, 2, 3]  →  "id IN (?, ?, ?)", [1, 2, 3]
    """
    field, lookup = (
        field_lookup.rsplit("__", 1)
        if "__" in field_lookup
        else (field_lookup, "exact")
    )

    if lookup not in LOOKUP_OPERATORS:
        raise ValueError(
            f"Неизвестный lookup '{lookup}'. Доступны: {list(LOOKUP_OPERATORS)}"
        )

    operator = LOOKUP_OPERATORS[lookup]

    if lookup == "in":
        value = list(value)
        placeholders = ", ".join(["?"] * len(value))
        return f"{field} {operator} ({placeholders})", value
    else:
        return f"{field} {operator} ?", [value]


def _compile_q(q: Q) -> tuple[str, list]:
    """Рекурсивно компилирует дерево Q в SQL-фрагмент.

    Каждый элемент q.children — либо кортеж (условие), либо Q (рекурсия).
    Результаты объединяются через q.connector (AND / OR / XOR).
    Если q.negated — оборачивается в NOT (...).
    """
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
        # SQLite не поддерживает XOR напрямую.
        # XOR(a, b) = (a OR b) AND NOT (a AND b)
        # params дублируются — каждая часть требует свои плейсхолдеры
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
    """Корневой Q → ('WHERE ...', params). Пустая строка если q_root is None."""
    if q_root is None:
        return "", []
    sql, params = _compile_q(q_root)
    return f"WHERE {sql}", params


def build_order_by(ordering: list[str]) -> str:
    """['-salary', 'age']  →  'ORDER BY salary DESC, age ASC'"""
    if not ordering:
        return ""
    clauses = []
    for field in ordering:
        if field.startswith("-"):
            clauses.append(f"{field[1:]} DESC")
        else:
            clauses.append(f"{field} ASC")
    return "ORDER BY " + ", ".join(clauses)


class QuerySet:
    """Ленивый набор запросов. Не ходит в БД до итерации или вызова
    терминального метода.

    Employee.objects
        .filter(salary__gte=10000)
        .exclude(grade="L1")
        .filter(Q(first_name__like="A%") | Q(last_name__like="B%"))
        .order_by("-salary")
    """

    def __init__(self, model_class, connection):
        self.model_class = model_class
        self.connection = connection
        self._q: Q | None = None
        self._ordering: list[str] = []
        self._result_cache = None

    def _clone(self) -> "QuerySet":
        qs = QuerySet(self.model_class, self.connection)
        qs._q = copy.deepcopy(self._q)
        qs._ordering = self._ordering.copy()
        return qs

    def _add_q(self, q: Q) -> "QuerySet":
        qs = self._clone()
        qs._result_cache = None
        qs._q = q if qs._q is None else qs._q & q
        return qs

    @staticmethod
    def _build_q(args, kwargs) -> Q:
        parts = list(args) + ([Q(**kwargs)] if kwargs else [])
        if not parts:
            raise ValueError("filter()/exclude() требуют хотя бы одного условия")
        result = parts[0]
        for part in parts[1:]:
            result = result & part
        return result

    # -- Публичный API -------------------------------------------------------

    def filter(self, *args, **kwargs) -> "QuerySet":
        """Добавляет AND-условие."""
        return self._add_q(self._build_q(args, kwargs))

    def exclude(self, *args, **kwargs) -> "QuerySet":
        """Добавляет NOT-условие."""
        return self._add_q(~self._build_q(args, kwargs))

    def order_by(self, *fields) -> "QuerySet":
        qs = self._clone()
        qs._ordering = list(fields)
        qs._result_cache = None
        return qs

    # -- Построение SQL ------------------------------------------------------

    def _build_select_sql(self) -> tuple[str, list]:
        where_sql, params = build_where(self._q)
        order_sql = build_order_by(self._ordering)
        query = " ".join(
            filter(
                None,
                [
                    f"SELECT * FROM {self.model_class.table_name}",
                    where_sql,
                    order_sql,
                ],
            )
        )
        return query, params

    # -- Терминальные методы (идут в БД) -------------------------------------

    def get(self, *args, **kwargs) -> object:
        """Возвращает ровно один объект или бросает исключение.

        Raises:
            DoesNotExist - если записей не найдено.
            MultipleObjectsReturned - если более одной записи.
        """
        qs = self.filter(*args, **kwargs) if (args or kwargs) else self
        results = qs._fetch()
        if not results:
            raise self.model_class.DoesNotExist(
                f"{self.model_class.__name__} не найден"
            )
        if len(results) > 1:
            raise self.model_class.MultipleObjectsReturned(
                f"Ожидался один объект, получено {len(results)}"
            )

        return results[0]

    def _fetch(self) -> list:
        """SELECT с кэшированием результата."""
        if self._result_cache is not None:
            return self._result_cache

        query, params = self._build_select_sql()
        cursor = self.connection.cursor()
        cursor.execute(query, params)

        col_names = tuple(desc[0] for desc in cursor.description)
        self._result_cache = [
            self.model_class(**dict(zip(col_names, row))) for row in cursor.fetchall()
        ]
        return self._result_cache

    def update(self, **new_data) -> int:
        """UPDATE с текущими фильтрами. Возвращает кол-во затронутых строк."""
        set_sql = ", ".join(f"{f} = ?" for f in new_data)
        where_sql, wparams = build_where(self._q)
        query = " ".join(
            filter(
                None,
                [
                    f"UPDATE {self.model_class.table_name}",
                    f"SET {set_sql}",
                    where_sql,
                ],
            )
        )
        cursor = self.connection.cursor()
        cursor.execute(query, list(new_data.values()) + wparams)
        self.connection.commit()
        return cursor.rowcount

    def delete(self) -> int:
        """DELETE с текущими фильтрами. Возвращает кол-во удалённых строк."""
        where_sql, params = build_where(self._q)
        query = " ".join(
            filter(
                None,
                [
                    f"DELETE FROM {self.model_class.table_name}",
                    where_sql,
                ],
            )
        )
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        self.connection.commit()
        return cursor.rowcount

    def count(self) -> int:
        where_sql, params = build_where(self._q)
        query = " ".join(
            filter(
                None,
                [
                    f"SELECT COUNT(*) FROM {self.model_class.table_name}",
                    where_sql,
                ],
            )
        )
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()[0]

    def first(self):
        results = self._fetch()
        return results[0] if results else None

    def exists(self) -> bool:
        return self.count() > 0

    # -- Протокол итерации ---------------------------------------------------

    def __iter__(self):
        return iter(self._fetch())

    def __len__(self):
        return len(self._fetch())

    def __getitem__(self, i):
        return self._fetch()[i]

    def __repr__(self) -> str:
        if self._result_cache is not None:
            suffix = " ..." if len(self._result_cache) > 3 else ""
            return f"<QuerySet {self._result_cache[:3]}{suffix}>"
        sql, params = self._build_select_sql()
        return f"<QuerySet (unevaluated) sql={sql!r}>"
