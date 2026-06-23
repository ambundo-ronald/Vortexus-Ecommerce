import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import SupplierOrderDetailPage from "../../../src/pages/supplier/SupplierOrderDetailPage";
import { supplierApi } from "../../../src/api/supplier.api";

const mockNotify = jest.fn();

jest.mock("../../../src/api/supplier.api", () => ({
  supplierApi: {
    order: jest.fn(),
    updateOrderLineStatus: jest.fn()
  }
}));

jest.mock("../../../src/store/ui.store", () => ({
  useUiStore: (selector) => selector({ notify: mockNotify })
}));

const orderPayload = {
  order: {
    group_id: 12,
    number: "100012",
    status: "processing",
    currency: "KES",
    customer: { name: "Customer One", email: "customer@example.com" },
    shipping_method: "Courier",
    tracking_reference: "",
    shipping_address: { line1: "Industrial Area", line4: "Nairobi" },
    supplier_totals: { item_count: 2, total_incl_tax: 830277.44 },
    lines: [
      {
        id: 88,
        title: "RO System",
        partner_sku: "RO-1000",
        status: "processing",
        quantity: 2,
        line_price_incl_tax: 830277.44
      }
    ]
  }
};

describe("SupplierOrderDetailPage", () => {
  beforeEach(() => {
    mockNotify.mockReset();
    supplierApi.order.mockReset();
    supplierApi.updateOrderLineStatus.mockReset();
    supplierApi.order.mockResolvedValue(orderPayload);
  });

  test("shows supplier totals and sends fulfillment updates using the backend payload", async () => {
    supplierApi.updateOrderLineStatus.mockResolvedValue({ detail: "Order line updated." });

    render(
      <MemoryRouter initialEntries={["/supplier/orders/100012"]}>
        <Routes>
          <Route path="/supplier/orders/:orderNumber" element={<SupplierOrderDetailPage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => expect(screen.getByRole("heading", { name: "100012" })).toBeInTheDocument());
    expect(screen.getByText("KES 830,277.44")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Status for RO System"), { target: { value: "shipped" } });
    fireEvent.change(screen.getByLabelText("Tracking reference for RO System"), { target: { value: "TRK-88" } });
    fireEvent.change(screen.getByLabelText("Fulfillment note for RO System"), { target: { value: "Collected by courier" } });
    fireEvent.click(screen.getByRole("button", { name: /update/i }));

    await waitFor(() => {
      expect(supplierApi.updateOrderLineStatus).toHaveBeenCalledWith("100012", 88, {
        status: "shipped",
        tracking_reference: "TRK-88",
        note: "Collected by courier"
      });
    });
    expect(mockNotify).toHaveBeenCalledWith(expect.objectContaining({ title: "Fulfillment updated" }));
  });
});
