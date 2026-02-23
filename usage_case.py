from ORM import BaseManager, BaseModel


class Employee(BaseModel):
    manager_class = BaseManager
    table_name = "employees"


# SQL: SELECT first_name, last_name, salary, grade FROM employees;
employees = Employee.objects.select(
    "first_name", "last_name", "salary", "grade"
)  # employees: List[Employee]

print(f"First select result:\n {employees} \n")


# SQL: INSERT INTO employees (first_name, last_name, salary)
#  	VALUES ('Yan', 'KIKI', 10000), ('Yoweri', 'ALOH', 15000);
employees_data = [
    {"first_name": "Yan", "last_name": "KIKI", "salary": 10000},
    {"first_name": "Yoweri", "last_name": "ALOH", "salary": 15000},
]
Employee.objects.bulk_insert(rows=employees_data)

employees = Employee.objects.select("first_name", "last_name", "salary", "grade")
print(f"Select result after bulk insert:\n {employees} \n")
