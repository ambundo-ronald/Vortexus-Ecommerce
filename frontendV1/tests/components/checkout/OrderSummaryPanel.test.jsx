import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import OrderSummaryPanel from "../../../src/components/checkout/OrderSummaryPanel";

describe("OrderSummaryPanel", () => {
  test("displays backend tax total and product tax state labels", () => {
    render(
      <MemoryRouter>
        <OrderSummaryPanel
          basket={{
            item_count: 2,
            currency: "KES",
            lines: [
              { id: 1, product_id: 10, quantity: 1, line_total: 1000, currency: "KES", product: { title: "Taxable pump" } },
              { id: 2, product_id: 20, quantity: 1, line_total: 500, currency: "KES", product: { title: "Exempt filter" } }
            ],
            tax_breakdown: {
              line_breakdown: [
                { product_id: 10, tax_status: "taxable", line_tax: 160 },
                { product_id: 20, tax_status: "tax_exempt", line_tax: 0 }
              ]
            }
          }}
          shipping={{
            totals: {
              subtotal: 1500,
              shipping: 100,
              taxes: { total_tax: 160 },
              order_total: 1760,
              currency: "KES"
            }
          }}
        />
      </MemoryRouter>
    );

    expect(screen.getByText("Tax")).toBeInTheDocument();
    expect(screen.getByText("Ksh 160.00")).toBeInTheDocument();
    expect(screen.getByText("Taxable / Tax exempt items included.")).toBeInTheDocument();
  });
});
