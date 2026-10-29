"""The service catalog: what each vehicle class needs, and how often."""
from dataclasses import dataclass

from .._generated import SERVICE_CATALOG


@dataclass(frozen=True)
class ServiceSpec:
    code: str
    name: str
    interval_miles: int
    interval_months: int
    classes: tuple

    def applies_to(self, vehicle_class):
        return vehicle_class in self.classes


def service_spec(code):
    name, miles, months, classes = SERVICE_CATALOG[code]
    return ServiceSpec(code, name, miles, months, classes)


def specs_for(vehicle_class):
    """Every service a vehicle of this class needs, in code order."""
    specs = (service_spec(code) for code in sorted(SERVICE_CATALOG))
    return [spec for spec in specs if spec.applies_to(vehicle_class)]
