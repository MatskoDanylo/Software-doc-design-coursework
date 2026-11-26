from collections.abc import Callable
from decimal import Decimal

import pytest

from app.models import PaymentStatus
from app.patterns.payment_gateway import (
    GatewayPayment,
    GatewayPaymentNotFound,
    GatewayStateConflict,
    MockGatewayAdapter,
    MockPaymentProvider,
    MockProviderError,
    PaymentGateway,
    PaymentGatewayError,
    PaymentOutcome,
    PaymentSimulator,
)


@pytest.fixture
def provider() -> MockPaymentProvider:
    return MockPaymentProvider()


@pytest.fixture
def adapter(provider: MockPaymentProvider) -> MockGatewayAdapter:
    return MockGatewayAdapter(provider)


def test_provider_speaks_its_own_dialect(provider: MockPaymentProvider) -> None:
    invoice = provider.open_invoice(9900, "980", "Premium", "payment-1")

    assert invoice["invoice_id"].startswith("inv_")
    assert (invoice["state"], invoice["sum"], invoice["ccy"], invoice["merchant_ref"]) == (
        "NEW",
        9900,
        "980",
        "payment-1",
    )
    assert provider.settle(invoice["invoice_id"], "hold")["state"] == "WAIT"
    assert provider.settle(invoice["invoice_id"], "approve")["state"] == "OK"
    assert provider.inspect(invoice["invoice_id"])["state"] == "OK"


def test_provider_returns_copies_of_its_records(provider: MockPaymentProvider) -> None:
    invoice = provider.open_invoice(100, "980", "x", "payment-1")
    invoice["state"] = "OK"

    assert provider.inspect(invoice["invoice_id"])["state"] == "NEW"


def test_provider_raises_its_own_errors(provider: MockPaymentProvider) -> None:
    with pytest.raises(MockProviderError) as exc:
        provider.inspect("inv_missing")
    assert exc.value.err_code == "E_NO_INVOICE"

    invoice = provider.open_invoice(100, "980", "x", "payment-1")
    provider.settle(invoice["invoice_id"], "decline")
    with pytest.raises(MockProviderError) as exc:
        provider.settle(invoice["invoice_id"], "approve")
    assert exc.value.err_code == "E_FINAL_STATE"


@pytest.mark.parametrize(
    ("call", "err_code"),
    [
        (lambda p: p.open_invoice(0, "980", "x", "payment-1"), "E_BAD_SUM"),
        (lambda p: p.open_invoice(100, "840", "x", "payment-1"), "E_BAD_CCY"),
        (lambda p: p.settle(p.open_invoice(100, "980", "x", "payment-1")["invoice_id"], "refund"), "E_BAD_SCENARIO"),
    ],
    ids=["non-positive-sum", "foreign-currency", "unknown-scenario"],
)
def test_provider_validates_its_input(
    provider: MockPaymentProvider, call: Callable[[MockPaymentProvider], object], err_code: str
) -> None:
    with pytest.raises(MockProviderError) as exc:
        call(provider)
    assert exc.value.err_code == err_code


def test_adapter_implements_target_and_simulator(adapter: MockGatewayAdapter) -> None:
    gateway: PaymentGateway = adapter
    simulator: PaymentSimulator = adapter

    assert gateway.provider_name == "mock"
    assert callable(simulator.simulate)


def test_create_payment_converts_hryvnias_to_kopiyky(
    adapter: MockGatewayAdapter, provider: MockPaymentProvider
) -> None:
    payment = adapter.create_payment(42, Decimal("99.00"), "UAH", "Premium, 30 днів")

    raw = provider.inspect(payment.external_id)
    assert (raw["sum"], raw["ccy"], raw["memo"], raw["merchant_ref"]) == (9900, "980", "Premium, 30 днів", "payment-42")
    assert payment == GatewayPayment(
        external_id=raw["invoice_id"], status=PaymentStatus.CREATED, amount=Decimal("99.00"), currency="UAH"
    )


def test_create_payment_keeps_kopiyky_exact(adapter: MockGatewayAdapter, provider: MockPaymentProvider) -> None:
    payment = adapter.create_payment(1, Decimal("149.99"), "UAH", "x")

    assert provider.inspect(payment.external_id)["sum"] == 14999
    assert payment.amount == Decimal("149.99")


def test_create_payment_rejects_fractions_of_a_kopiyka(adapter: MockGatewayAdapter) -> None:
    with pytest.raises(ValueError, match="fractions of a kopiyka"):
        adapter.create_payment(1, Decimal("99.005"), "UAH", "x")


def test_create_payment_rejects_unsupported_currency(adapter: MockGatewayAdapter) -> None:
    with pytest.raises(ValueError, match="EUR"):
        adapter.create_payment(1, Decimal("10.00"), "EUR", "x")


def test_provider_validation_error_becomes_gateway_error(adapter: MockGatewayAdapter) -> None:
    with pytest.raises(PaymentGatewayError, match="E_BAD_SUM") as exc:
        adapter.create_payment(1, Decimal("0.00"), "UAH", "x")

    assert (exc.value.status_code, exc.value.code) == (502, "payment_gateway_error")


@pytest.mark.parametrize(
    ("outcome", "status"),
    [
        (PaymentOutcome.SUCCESS, PaymentStatus.SUCCESS),
        (PaymentOutcome.PENDING, PaymentStatus.PENDING),
        (PaymentOutcome.FAILED, PaymentStatus.FAILED),
    ],
)
def test_simulate_maps_outcome_to_scenario_and_state_to_status(
    adapter: MockGatewayAdapter, outcome: PaymentOutcome, status: PaymentStatus
) -> None:
    payment = adapter.create_payment(1, Decimal("99.00"), "UAH", "x")

    assert adapter.simulate(payment.external_id, outcome).status == status
    assert adapter.get_status(payment.external_id) == status


def test_pending_payment_can_be_completed_later(adapter: MockGatewayAdapter) -> None:
    payment = adapter.create_payment(1, Decimal("99.00"), "UAH", "x")
    adapter.simulate(payment.external_id, PaymentOutcome.PENDING)

    assert adapter.simulate(payment.external_id, PaymentOutcome.SUCCESS).status == PaymentStatus.SUCCESS


def test_get_status_of_new_invoice_is_created(adapter: MockGatewayAdapter) -> None:
    payment = adapter.create_payment(1, Decimal("99.00"), "UAH", "x")

    assert adapter.get_status(payment.external_id) == PaymentStatus.CREATED


def test_unknown_invoice_becomes_gateway_payment_not_found(adapter: MockGatewayAdapter) -> None:
    with pytest.raises(GatewayPaymentNotFound) as exc:
        adapter.get_status("inv_missing")
    assert (exc.value.status_code, exc.value.code) == (502, "gateway_payment_not_found")

    with pytest.raises(GatewayPaymentNotFound):
        adapter.simulate("inv_missing", PaymentOutcome.SUCCESS)


def test_settling_final_invoice_becomes_state_conflict(adapter: MockGatewayAdapter) -> None:
    payment = adapter.create_payment(1, Decimal("99.00"), "UAH", "x")
    adapter.simulate(payment.external_id, PaymentOutcome.FAILED)

    with pytest.raises(GatewayStateConflict) as exc:
        adapter.simulate(payment.external_id, PaymentOutcome.SUCCESS)

    assert exc.value.status_code == 409


def test_unknown_provider_state_is_a_gateway_error(adapter: MockGatewayAdapter, provider: MockPaymentProvider) -> None:
    payment = adapter.create_payment(1, Decimal("99.00"), "UAH", "x")
    provider._invoices[payment.external_id]["state"] = "REFUNDED"

    with pytest.raises(PaymentGatewayError, match="REFUNDED"):
        adapter.get_status(payment.external_id)


def test_unknown_provider_currency_is_a_gateway_error(
    adapter: MockGatewayAdapter, provider: MockPaymentProvider
) -> None:
    payment = adapter.create_payment(1, Decimal("99.00"), "UAH", "x")
    provider._invoices[payment.external_id]["ccy"] = "840"

    with pytest.raises(PaymentGatewayError, match="840"):
        adapter.simulate(payment.external_id, PaymentOutcome.SUCCESS)


def test_payment_status_finality() -> None:
    assert [s for s in PaymentStatus if s.is_final] == [PaymentStatus.SUCCESS, PaymentStatus.FAILED]
