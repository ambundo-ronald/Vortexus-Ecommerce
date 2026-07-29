import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import CartSummary from "../../../src/components/cart/CartSummary";

jest.mock("../../../src/store/cart.store", () => ({
  useCartStore: (selector) =>
    selector({
      applyVoucher: jest.fn(),
      removeVoucher: jest.fn(),
      loading: false
    })
}));

describe("CartSummary", () => {
  test("shows tax state and keeps coupon discount in estimated total", () => {
    render(
      <MemoryRouter>
        <CartSummary
          basket={{
            item_count: 1,
            currency: "KES",
            totals: {
              subtotal: 1000,
              discount: 100,
              taxes: { total_tax: 0 },
              currency: "KES"
            },
            tax_breakdown: {
              line_breakdown: [{ tax_status: "zero_rated", line_tax: 0 }]
            },
            vouchers: []
          }}
        />
      </MemoryRouter>
    );

    expect(screen.getByText("Tax")).toBeInTheDocument();
    expect(screen.getByText("Zero-rated")).toBeInTheDocument();
    expect(screen.getByText("Ksh 900.00")).toBeInTheDocument();
  });
});
