import { fireEvent, render, screen } from "@testing-library/react";

import PaymentMethodSelector from "../../../src/components/checkout/PaymentMethodSelector";

describe("PaymentMethodSelector", () => {
  test("submits the selected offline method and receipt email", () => {
    const onSubmit = jest.fn();
    render(
      <PaymentMethodSelector
        methods={[
          {
            code: "cash_on_delivery",
            name: "Cash on delivery",
            requires_prepayment: false,
            is_sandbox: false
          }
        ]}
        defaultEmail="buyer@example.com"
        onSubmit={onSubmit}
      />
    );

    fireEvent.click(screen.getByRole("button", { name: /continue to review/i }));

    expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({
      method: "cash_on_delivery",
      payerEmail: "buyer@example.com"
    }));
  });

  test("shows explicit sandbox messaging for non-production card flows", () => {
    render(
      <PaymentMethodSelector
        methods={[
          {
            code: "credit_card",
            name: "Credit card",
            requires_prepayment: true,
            is_sandbox: true
          }
        ]}
      />
    );

    expect(screen.getByText(/sandbox card token flow/i)).toBeInTheDocument();
    expect(screen.getByText("Test")).toBeInTheDocument();
  });
});
