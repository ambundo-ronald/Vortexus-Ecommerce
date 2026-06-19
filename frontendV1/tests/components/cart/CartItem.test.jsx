import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import CartItem from "../../../src/components/cart/CartItem";

jest.mock("../../../src/store/cart.store", () => {
  const state = {
    updateLine: jest.fn(),
    removeLine: jest.fn(),
    saveLineForLater: jest.fn(),
    loading: false
  };

  return {
    useCartStore: (selector) => selector(state)
  };
});

jest.mock("../../../src/utils/productImages", () => ({
  productImageUrl: () => ""
}));

describe("CartItem", () => {
  test("links the basket line to its nested product detail page", () => {
    render(
      <MemoryRouter>
        <CartItem
          line={{
            id: 12,
            line_reference: "line-12",
            quantity: 1,
            unit_price: 830277.44,
            line_total: 830277.44,
            currency: "KES",
            available_quantity: 11,
            availability: { is_available: true },
            product: {
              id: 91,
              title: "1000LPH RO System",
              sku: "RO-1000",
              in_stock: true,
              stock_count: 11
            }
          }}
        />
      </MemoryRouter>
    );

    const productLinks = screen.getAllByRole("link", { name: /1000LPH RO System/i });
    expect(productLinks.length).toBeGreaterThan(0);
    productLinks.forEach((link) => {
      expect(link).toHaveAttribute("href", "/products/91");
    });
  });
});
