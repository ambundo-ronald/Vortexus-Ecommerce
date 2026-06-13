import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import SupplierOrdersPage from "../../../src/pages/supplier/SupplierOrdersPage";
import { supplierApi } from "../../../src/api/supplier.api";

jest.mock("../../../src/api/supplier.api", () => ({
  supplierApi: {
    orders: jest.fn()
  }
}));

describe("SupplierOrdersPage", () => {
  beforeEach(() => {
    supplierApi.orders.mockReset();
  });

  test("renders supplier-scoped item counts and totals from the backend contract", async () => {
    supplierApi.orders.mockResolvedValue({
      results: [
        {
          group_id: 41,
          number: "100041",
          status: "processing",
          date_placed: "2026-06-13T08:00:00Z",
          currency: "KES",
          supplier_item_count: 7,
          supplier_total_incl_tax: 1200
        }
      ]
    });

    render(
      <MemoryRouter>
        <SupplierOrdersPage />
      </MemoryRouter>
    );

    await waitFor(() => expect(screen.getByText("100041")).toBeInTheDocument());
    expect(screen.getByText("7")).toBeInTheDocument();
    expect(screen.getByText("KES 1,200")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /view/i })).toHaveAttribute("href", "/supplier/orders/100041");
  });
});
