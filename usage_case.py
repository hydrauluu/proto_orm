from Base import BaseModel
from Manager import BaseManager
from fields import IntegerField, CharField
from Q import Q


class Employee(BaseModel):
    table_name = "employees"
    manager_class = BaseManager

    first_name = CharField(max_length=255)
    last_name = CharField(max_length=255)
    salary = IntegerField(min_value=0)
    garde = CharField(max_length=10)


# SELECT все записи
employees = Employee.objects.all()
print(f"Все сотрудники:\n {employees}\n")

# SELECT с filter
employees = Employee.objects.filter(salary__gte=13000)
print(f"Зарплата >= 13000:\n {employees}\n")

# SELECT с exclude
employees = Employee.objects.filter(salary__gte=13000).exclude(grade="L3")
print(f"Зарплата >= 13000, не L3:\n {employees}\n")

# SELECT с Q (OR)
employees = Employee.objects.filter(Q(grade="L2") | Q(grade="L3"))
print(f"Grade L2 или L3:\n {employees}\n")

# SELECT с order_by
employees = Employee.objects.order_by("-salary")
print(f"Отсортировано по убыванию salary:\n {employees}\n")

# get - один объект
try:
    emp = Employee.objects.get(first_name="Renaud")
    print(f"get(): {emp}\n")
except Employee.DoesNotExist as e:
    print(e)

# INSERT
Employee.objects.bulk_insert(
    [
        {"first_name": "Yan", "last_name": "KIKI", "salary": 10000, "grade": "L1"},
        {"first_name": "Yoweri", "last_name": "ALOH", "salary": 15000, "grade": "L2"},
    ]
)
print(f"После bulk_insert:\n {Employee.objects.all()}\n")

# UPDATE
Employee.objects.filter(grade="L1").update(salary=12000)
print(f"После update L1 → salary=12000:\n {Employee.objects.all()}\n")

# DELETE
Employee.objects.filter(grade="L1").delete()
print(f"После delete grade=L1:\n {Employee.objects.all()}\n")

# count / exists / first
print(f"count L2: {Employee.objects.filter(grade='L2').count()}")
print(f"exists L5: {Employee.objects.filter(grade='L5').exists()}")
print(f"first по salary: {Employee.objects.order_by('salary').first()}")
