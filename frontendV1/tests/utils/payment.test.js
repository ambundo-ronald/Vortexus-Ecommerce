import {
  isPaymentComplete,
  isPaymentFailed,
  paymentReferenceFromSearch,
  paymentRequiresPrepayment,
  paymentStatusView,
  readPendingCheckout,
  readablePaymentMethod
} from "../../src/utils/payment";

describe("payment utilities", () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  test("classifies terminal payment states", () => {
    expect(isPaymentComplete({ status: "paid" })).toBe(true);
    expect(isPaymentComplete("authorized")).toBe(true);
    expect(isPaymentFailed({ status: "failed" })).toBe(true);
    expect(isPaymentFailed("cancelled")).toBe(true);
    expect(isPaymentComplete("pending")).toBe(false);
  });

  test("uses method metadata before the fallback prepayment list", () => {
    expect(paymentRequiresPrepayment({ code: "mpesa", requires_prepayment: true })).toBe(true);
    expect(paymentRequiresPrepayment({ code: "mpesa", requires_prepayment: false })).toBe(false);
    expect(paymentRequiresPrepayment("pesapal")).toBe(true);
    expect(paymentRequiresPrepayment("cash_on_delivery")).toBe(false);
  });

  test("creates customer-facing labels and provider messages", () => {
    expect(readablePaymentMethod("cash_on_delivery")).toBe("Cash On Delivery");
    expect(paymentStatusView({
      method: "mpesa",
      status: "pending",
      provider_payload: { customer_message: "Enter your PIN" }
    })).toMatchObject({
      label: "Pending",
      message: "Enter your PIN"
    });
  });

  test("recovers a Pesapal callback reference without navigation state", () => {
    const searchParams = new URLSearchParams("OrderMerchantReference=PAY-RETURN-1");

    expect(paymentReferenceFromSearch(searchParams)).toBe("PAY-RETURN-1");
    expect(readPendingCheckout(searchParams)).toMatchObject({
      payment_reference: "PAY-RETURN-1",
      payment: {
        reference: "PAY-RETURN-1",
        method: "pesapal",
        status: "pending"
      }
    });
  });
});
