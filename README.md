# Simple Python ORM

Простая ORM библиотека на Python для работы с базой данных SQLite. 
Проект нацелен на выполнение основных CRUD операций.

## Реализованный функционал

На данный момент реализованы следующие операции:
- **SELECT**: Выборка данных из таблицы.
- **INSERT**: Добавление новых записей (bulk insert).
- **UPDATE**: Обновление существующих записей.
- **DELETE**: Удаление всех записей.

# Запланированные функции
- Внедрение условия WHERE для операций SELECT, UPDATE и DELETE.

## Использование

Для начала работы необходимо создать базу данных и тестовые таблицы.

1. **Инициализация БД**:
   Запустите скрипт `make_db.py`, чтобы создать файл базы данных `my_database.db` и заполнить его начальными данными.
   ```bash
   python make_db.py
   ```

2. **Запуск примера**:
   Используйте `usage_case.py` для проверки работы ORM.
   ```bash
   python usage_case.py
   ```

## Пример кода

```python
from ORM import BaseModel, BaseManager

# Определение модели
class Employee(BaseModel):
    manager_class = BaseManager
    table_name = "employees"

# 1. Выборка данных (SELECT)
employees = Employee.objects.select("first_name", "last_name", "salary")
print(employees)

# 2. Добавление данных (INSERT)
new_employees = [
    {"first_name": "Yan", "last_name": "KIKI", "salary": 10000},
    {"first_name": "Yoweri", "last_name": "ALOH", "salary": 15000},
]
Employee.objects.bulk_insert(rows=new_employees)

# 3. Удаление данных (DELETE)
Employee.objects.delete()

# 4. Обновление данных (UPDATE)
Employee.objects.update(new_data={"salary": 17000, "grade": "L2"})
```
