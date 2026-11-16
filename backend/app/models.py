from decimal import Decimal
from typing import Annotated
from pydantic import BaseModel, Field, ConfigDict, StringConstraints

EmailAddress = Annotated[
    str, StringConstraints(max_length=254, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Login(Model):
    email: EmailAddress
    password: str = Field(min_length=1, max_length=72)


class Register(Login):
    name: str = Field(min_length=2, max_length=100)
    phone: str = ""


class RequestInput(Model):
    service: str = Field(min_length=2, max_length=100)
    property_type: str = Field(min_length=2, max_length=100)
    location: str = Field(min_length=3, max_length=500)
    area: float = Field(gt=0, le=10000000)
    rooms: int = Field(default=1, ge=0, le=10000)
    description: str = Field(min_length=10, max_length=10000)
    preferred_date: str = ""
    requirements: str = Field(default="", max_length=5000)
    file_ids: list[str] = Field(default_factory=list, max_length=20)


class InspectionInput(Model):
    date: str = Field(min_length=10, max_length=40)
    measurements: str = Field(min_length=2, max_length=5000)
    notes: str = Field(min_length=2, max_length=5000)
    materials: str = Field(default="", max_length=5000)
    completed: bool = False
    file_ids: list[str] = Field(default_factory=list, max_length=20)


class BOQItem(Model):
    description: str = Field(min_length=2, max_length=500)
    category: str = Field(pattern="^(Material|Labour|Other)$")
    quantity: Decimal = Field(gt=0, max_digits=12, decimal_places=3)
    unit: str = Field(min_length=1, max_length=30)
    unit_price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)


class QuoteInput(Model):
    phase: int = Field(ge=1, le=100)
    title: str = Field(min_length=2, max_length=200)
    description: str = Field(min_length=5, max_length=10000)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    duration: int = Field(ge=1, le=3650)
    pdf_id: str
    items: list[BOQItem] = Field(default_factory=list, max_length=100)
    tax_percent: Decimal = Field(
        default=Decimal("0"), ge=0, le=100, max_digits=5, decimal_places=2
    )
    discount: Decimal = Field(
        default=Decimal("0"), ge=0, max_digits=12, decimal_places=2
    )
    terms: str = Field(min_length=3, max_length=5000)


class Decision(Model):
    decision: str


class ProjectInput(Model):
    quote_id: str
    title: str = Field(min_length=3, max_length=200)
    manager_id: str
    start_date: str = Field(min_length=10, max_length=10)
    deadline: str = Field(min_length=10, max_length=10)


class Assignment(Model):
    worker_id: str


class MilestoneInput(Model):
    title: str = Field(min_length=2, max_length=200)
    description: str = Field(default="", max_length=2000)
    phase: int = Field(ge=1)
    deadline: str = Field(min_length=10, max_length=10)


class Progress(Model):
    progress: int = Field(ge=0, le=100)


class TaskInput(Model):
    title: str = Field(min_length=2, max_length=200)
    description: str = Field(default="", max_length=5000)
    worker_id: str
    deadline: str = Field(min_length=10, max_length=10)
    priority: str = Field(default="Normal", pattern="^(Normal|High|Urgent)$")


class MessageInput(Model):
    text: str = Field(default="", max_length=5000)
    file_id: str | None = None
    issue: bool = False


class Verify(Model):
    approved: bool
    share: bool = False
    text: str = Field(default="", max_length=5000)


class PaymentInput(Model):
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    date: str = Field(min_length=10, max_length=10)
    method: str
    reference: str = Field(default="", max_length=200)
    notes: str = Field(default="", max_length=2000)
    verification: str = Field(min_length=5, max_length=2000)
    idempotency_key: str = Field(min_length=8, max_length=100)


class Profile(Model):
    email: EmailAddress | None = None
    name: str = Field(min_length=2, max_length=100)
    phone: str = Field(default="", max_length=100)
    address: str = Field(default="", max_length=500)
    password: str = Field(default="", max_length=72)


class Employee(Register):
    role: str


class Feedback(Model):
    rating: int = Field(ge=1, le=5)
    text: str = Field(min_length=5, max_length=2000)


class PhaseInput(Model):
    title: str = Field(min_length=2, max_length=200)
    start_date: str = Field(min_length=10, max_length=10)
    deadline: str = Field(min_length=10, max_length=10)
    status: str


class Reassign(Model):
    manager_id: str


class ServiceInput(Model):
    name: str = Field(min_length=2, max_length=100)
    description: str = Field(min_length=10, max_length=5000)
    active: bool = True


class RequestStatus(Model):
    status: str
    note: str = Field(min_length=3, max_length=2000)


class MaterialInput(Model):
    name: str = Field(min_length=2, max_length=200)
    quantity: float = Field(gt=0, le=10000000)
    unit: str = Field(min_length=1, max_length=30)
    status: str
    notes: str = Field(default="", max_length=2000)


class QualityInput(Model):
    title: str = Field(min_length=3, max_length=200)
    passed: bool
    defects: str = Field(default="", max_length=5000)
    corrective_action: str = Field(default="", max_length=5000)


class Enquiry(Model):
    name: str = Field(min_length=2, max_length=100)
    email: EmailAddress
    phone: str = Field(default="", max_length=100)
    message: str = Field(min_length=5, max_length=5000)


class RequestReply(Model):
    text: str = Field(min_length=5, max_length=5000)
    file_ids: list[str] = Field(default_factory=list, max_length=20)


class EmployeeDetails(Model):
    name: str = Field(min_length=2, max_length=100)
    email: EmailAddress
    phone: str = Field(default="", max_length=100)
