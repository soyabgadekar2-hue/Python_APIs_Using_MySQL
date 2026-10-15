import re
from decimal import Decimal, InvalidOperation

import mysql.connector
from fastapi import Body, FastAPI, HTTPException, Path, Response
from fastapi.responses import JSONResponse
from mysql.connector import errorcode

import employee_queries


app = FastAPI(title="Employee Management API")


@app.exception_handler(mysql.connector.Error)
async def handle_database_error(request, error):
    return JSONResponse(
        status_code=503,
        content={"detail": "The database is unavailable. Please try again."},
    )


def validate_employee_data(employee):
    required_fields = ("name", "email", "department", "salary")
    missing_fields = [field for field in required_fields if field not in employee]
    if missing_fields:
        raise HTTPException(
            status_code=422,
            detail=f"Missing required fields: {', '.join(missing_fields)}",
        )

    name = employee["name"]
    department = employee["department"]
    email = employee["email"]

    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 100:
        raise HTTPException(
            status_code=422,
            detail="name must contain between 1 and 100 characters.",
        )
    if not isinstance(department, str) or not 1 <= len(department.strip()) <= 100:
        raise HTTPException(
            status_code=422,
            detail="department must contain between 1 and 100 characters.",
        )
    if (
        not isinstance(email, str)
        or len(email) > 255
        or re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email.strip()) is None
    ):
        raise HTTPException(status_code=422, detail="email must be a valid email address.")

    salary_value = employee["salary"]
    if isinstance(salary_value, bool):
        raise HTTPException(status_code=422, detail="salary must be a number.")
    try:
        salary = Decimal(str(salary_value))
    except (InvalidOperation, ValueError):
        raise HTTPException(status_code=422, detail="salary must be a valid number.") from None

    if not salary.is_finite() or salary < 0 or salary > Decimal("99999999.99"):
        raise HTTPException(
            status_code=422,
            detail="salary must be between 0 and 99999999.99.",
        )
    if salary.as_tuple().exponent < -2:
        raise HTTPException(
            status_code=422,
            detail="salary can have at most two decimal places.",
        )

    return {
        "name": name.strip(),
        "email": email.strip(),
        "department": department.strip(),
        "salary": str(salary),
    }


def raise_duplicate_email_error(error):
    if error.errno == errorcode.ER_DUP_ENTRY:
        raise HTTPException(
            status_code=409,
            detail="An employee with this email already exists.",
        ) from error
    raise error


@app.post("/employees", status_code=201)
def create_employee(employee: dict = Body(...)):
    employee_data = validate_employee_data(employee)
    try:
        return employee_queries.create_employee(employee_data)
    except mysql.connector.IntegrityError as error:
        raise_duplicate_email_error(error)


@app.get("/employees")
def get_all_employees():
    return employee_queries.get_all_employees()


@app.get("/employees/{employee_id}")
def get_employee_by_id(employee_id: int = Path(gt=0)):
    employee = employee_queries.get_employee_by_id(employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found.")
    return employee


@app.put("/employees/{employee_id}")
def update_employee(employee: dict = Body(...), employee_id: int = Path(gt=0)):
    employee_data = validate_employee_data(employee)
    try:
        updated_employee = employee_queries.update_employee(employee_id, employee_data)
    except mysql.connector.IntegrityError as error:
        raise_duplicate_email_error(error)

    if updated_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found.")
    return updated_employee


@app.delete("/employees/{employee_id}", status_code=204)
def delete_employee(employee_id: int = Path(gt=0)):
    deleted = employee_queries.delete_employee(employee_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Employee not found.")
    return Response(status_code=204)