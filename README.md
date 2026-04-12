# Simple Python ORM

Учебная ORM-библиотека на чистом Python для работы с SQLite.  
Архитектура вдохновлена Django ORM — QuerySet, Q-объекты, ленивые запросы.

---

## Структура проекта

```
project/
├── Q.py           — Q-объект: дерево условий с операторами &, |, ^, ~
├── queryset.py    — QuerySet: ленивая выборка + SQL-компилятор
├── Manager.py     — BaseManager: точка входа (Model.objects)
├── Base.py        — MetaModel + BaseModel: базовые классы моделей
├── fields.py      — дескрипторы полей: IntegerField, CharField, FloatField
├── make_db.py     — создание тестовой БД
└── usage_case.py  — примеры использования
```

---

## Быстрый старт

**1. Создать БД:**
```bash
python make_db.py
```

**2. Запустить примеры:**
```bash
python usage_case.py
```

---

## Определение модели

```python
from Base import BaseModel
from Manager import BaseManager
from fields import IntegerField, CharField

class Employee(BaseModel):
    table_name    = "employees"
    manager_class = BaseManager

    # Опционально — дескрипторы с валидацией
    salary = IntegerField(min_value=0)
    grade  = CharField(max_length=10)
```

---

## CRUD

### SELECT

```python
# Все записи
Employee.objects.all()

# С фильтром
Employee.objects.filter(salary__gte=13000)

# Цепочка условий
Employee.objects.filter(salary__gte=10000).exclude(grade="L1").order_by("-salary")
```

### INSERT

```python
Employee.objects.bulk_insert([
    {"first_name": "Alice", "last_name": "Smith", "salary": 13000, "grade": "L2"},
    {"first_name": "Bob",   "last_name": "Jones", "salary": 16000, "grade": "L3"},
])
```

### UPDATE

```python
# Обновить конкретные записи
Employee.objects.filter(grade="L1").update(salary=12000)
```

### DELETE

```python
# Удалить по условию
Employee.objects.filter(grade="L1").delete()
```

---

## Q-объекты

Позволяют строить сложные условия с OR, AND, XOR и отрицанием.

```python
from Q import Q

# OR
Employee.objects.filter(Q(grade="L1") | Q(grade="L2"))

# AND явный
Employee.objects.filter(Q(salary__gte=10000) & Q(grade="L2"))

# NOT
Employee.objects.filter(~Q(grade="L1"))

# XOR — ровно одно из условий истинно
Employee.objects.filter(Q(grade="L2") ^ Q(grade="L3"))

# Комбинация
Employee.objects.filter(
    Q(salary__gte=10000) & (Q(grade="L2") | Q(grade="L3"))
)
```

---

## Lookup-операторы

| Синтаксис         | SQL              |
|-------------------|------------------|
| `field=value`     | `field = ?`      |
| `field__exact=v`  | `field = ?`      |
| `field__ne=v`     | `field != ?`     |
| `field__lt=v`     | `field < ?`      |
| `field__lte=v`    | `field <= ?`     |
| `field__gt=v`     | `field > ?`      |
| `field__gte=v`    | `field >= ?`     |
| `field__like=v`   | `field LIKE ?`   |
| `field__in=[...]` | `field IN (...)`  |

---

## Терминальные методы QuerySet

| Метод        | Описание                          |
|--------------|-----------------------------------|
| `all()`      | Все записи                        |
| `filter()`   | Фильтрация (AND)                  |
| `exclude()`  | Исключение (NOT)                  |
| `order_by()` | Сортировка (`-field` = DESC)      |
| `first()`    | Первая запись или None            |
| `count()`    | Количество записей                |
| `exists()`   | True если есть хоть одна запись   |
| `update()`   | Обновление, возвращает кол-во строк |
| `delete()`   | Удаление, возвращает кол-во строк  |

---

## Дескрипторы полей

```python
from fields import IntegerField, FloatField, CharField

class Product(BaseModel):
    table_name = "products"

    price    = FloatField(min_value=0.0)
    quantity = IntegerField(min_value=0, max_value=9999)
    name     = CharField(max_length=255)
```

Дескрипторы валидируют значения при присвоении и бросают `TypeError` / `ValueError` при нарушении ограничений.

---

## Запланировано

- `exclude()` с OR внутри блока
- `ForeignKey` и связанные модели
- Автогенерация `CREATE TABLE` из полей модели
- Транзакции через контекстный менеджер
- Миграции
