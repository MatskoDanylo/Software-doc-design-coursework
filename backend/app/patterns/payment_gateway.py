from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from threading import Lock
from typing import Any, ClassVar, Protocol
from uuid import uuid4

from app.core.errors import BadGatewayError, ConflictError
from app.models import PaymentStatus


class PaymentOutcome(StrEnum):
    SUCCESS = "success"
    PENDING = "pending"
    FAILED = "failed"


@dataclass(frozen=True)
class GatewayPayment:
    external_id: str
    status: PaymentStatus
    amount: Decimal
    currency: str


class PaymentGatewayError(BadGatewayError):
    code = "payment_gateway_error"


class GatewayPaymentNotFound(PaymentGatewayError):
    code = "gateway_payment_not_found"


class GatewayStateConflict(ConflictError):
    code = "gateway_state_conflict"


class PaymentGateway(Protocol):
    provider_name: str

    def create_payment(self, payment_id: int, amount: Decimal, currency: str, description: str) -> GatewayPayment: ...

    def get_status(self, external_id: str) -> PaymentStatus: ...


class PaymentSimulator(Protocol):
    def simulate(self, external_id: str, outcome: PaymentOutcome) -> GatewayPayment: ...


class MockProviderError(Exception):
    def __init__(self, err_code: str, text: str) -> None:
        super().__init__(f"{err_code}: {text}")
        self.err_code = err_code
        self.text = text


class MockPaymentProvider:
    """Stand-in for a third-party acquiring SDK: kopiyky, ISO 4217 numeric codes, string states, plain dicts."""

    _FINAL_STATES = frozenset({"OK", "DECLINED"})
    _SCENARIOS: ClassVar[dict[str, str]] = {"approve": "OK", "hold": "WAIT", "decline": "DECLINED"}

    def __init__(self) -> None:
        self._invoices: dict[str, dict[str, Any]] = {}
        self._lock = Lock()

    def open_invoice(self, sum_kop: int, ccy: str, memo: str, merchant_ref: str) -> dict[str, Any]:
        if sum_kop <= 0:
            raise MockProviderError("E_BAD_SUM", "sum must be a positive number of kopiyky")
        if ccy != "980":
            raise MockProviderError("E_BAD_CCY", f"currency {ccy} is not accepted")
        invoice = {
            "invoice_id": f"inv_{uuid4().hex}",
            "state": "NEW",
            "sum": sum_kop,
            "ccy": ccy,
            "memo": memo,
            "merchant_ref": merchant_ref,
        }
        with self._lock:
            self._invoices[invoice["invoice_id"]] = invoice
            return dict(invoice)

    def settle(self, invoice_id: str, scenario: str) -> dict[str, Any]:
        state = self._SCENARIOS.get(scenario)
        if state is None:
            raise MockProviderError("E_BAD_SCENARIO", f"unknown scenario {scenario}")
        with self._lock:
            invoice = self._find(invoice_id)
            if invoice["state"] in self._FINAL_STATES:
                raise MockProviderError("E_FINAL_STATE", f"invoice is already {invoice['state']}")
            invoice["state"] = state
            return dict(invoice)

    def inspect(self, invoice_id: str) -> dict[str, Any]:
        with self._lock:
            return dict(self._find(invoice_id))

    def _find(self, invoice_id: str) -> dict[str, Any]:
        invoice = self._invoices.get(invoice_id)
        if invoice is None:
            raise MockProviderError("E_NO_INVOICE", f"invoice {invoice_id} does not exist")
        return invoice


class MockGatewayAdapter:
    provider_name = "mock"

    _CURRENCIES: ClassVar[dict[str, str]] = {"UAH": "980"}
    _STATUSES: ClassVar[dict[str, PaymentStatus]] = {
        "NEW": PaymentStatus.CREATED,
        "WAIT": PaymentStatus.PENDING,
        "OK": PaymentStatus.SUCCESS,
        "DECLINED": PaymentStatus.FAILED,
    }
    _SCENARIOS: ClassVar[dict[PaymentOutcome, str]] = {
        PaymentOutcome.SUCCESS: "approve",
        PaymentOutcome.PENDING: "hold",
        PaymentOutcome.FAILED: "decline",
    }

    def __init__(self, provider: MockPaymentProvider) -> None:
        self.provider = provider

    def create_payment(self, payment_id: int, amount: Decimal, currency: str, description: str) -> GatewayPayment:
        invoice = self._call(
            self.provider.open_invoice, _to_kopiyky(amount), self._ccy(currency), description, f"payment-{payment_id}"
        )
        return self._to_payment(invoice)

    def get_status(self, external_id: str) -> PaymentStatus:
        return self._status(self._call(self.provider.inspect, external_id)["state"])

    def simulate(self, external_id: str, outcome: PaymentOutcome) -> GatewayPayment:
        return self._to_payment(self._call(self.provider.settle, external_id, self._SCENARIOS[outcome]))

    def _ccy(self, currency: str) -> str:
        code = self._CURRENCIES.get(currency)
        if code is None:
            raise ValueError(f"Currency {currency} is not supported by the mock gateway")
        return code

    def _currency(self, ccy: str) -> str:
        for currency, code in self._CURRENCIES.items():
            if code == ccy:
                return currency
        raise PaymentGatewayError(f"Payment provider returned unknown currency {ccy}")

    def _status(self, state: str) -> PaymentStatus:
        status = self._STATUSES.get(state)
        if status is None:
            raise PaymentGatewayError(f"Payment provider returned unknown state {state}")
        return status

    def _to_payment(self, invoice: dict[str, Any]) -> GatewayPayment:
        return GatewayPayment(
            external_id=invoice["invoice_id"],
            status=self._status(invoice["state"]),
            amount=_from_kopiyky(invoice["sum"]),
            currency=self._currency(invoice["ccy"]),
        )

    @staticmethod
    def _call[**P](method: Callable[P, dict[str, Any]], *args: P.args, **kwargs: P.kwargs) -> dict[str, Any]:
        try:
            return method(*args, **kwargs)
        except MockProviderError as exc:
            raise _translate(exc) from exc


def _translate(exc: MockProviderError) -> Exception:
    if exc.err_code == "E_NO_INVOICE":
        return GatewayPaymentNotFound(f"Payment provider does not know this invoice: {exc.text}")
    if exc.err_code == "E_FINAL_STATE":
        return GatewayStateConflict(f"Payment provider refused to change a final invoice: {exc.text}")
    return PaymentGatewayError(f"Payment provider error {exc.err_code}: {exc.text}")


def _to_kopiyky(amount: Decimal) -> int:
    kopiyky = amount * 100
    if kopiyky != kopiyky.to_integral_value():
        raise ValueError(f"Amount {amount} has fractions of a kopiyka")
    return int(kopiyky)


def _from_kopiyky(kopiyky: int) -> Decimal:
    return (Decimal(kopiyky) / 100).quantize(Decimal("0.01"))
