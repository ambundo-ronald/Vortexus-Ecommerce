import { normalizeCheckoutTotals } from "./checkoutTotals";

describe("normalizeCheckoutTotals", () => {
  it("trusts explicit basket order totals after discounts", () => {
    const totals = normalizeCheckoutTotals({
      basket: {
        totals: {
          subtotal: 1160,
          discount: 160,
          tax: 160,
          order_total: 1000,
          currency: "KES"
        }
      }
    });

    expect(totals.subtotal).toBe(1160);
    expect(totals.discount).toBe(160);
    expect(totals.tax).toBe(160);
    expect(totals.order_total).toBe(1000);
  });

  it("does not add informational tax again when falling back", () => {
    const totals = normalizeCheckoutTotals({
      basket: {
        totals: {
          subtotal: 1160,
          discount: 160,
          tax: 160,
          currency: "KES"
        }
      }
    });

    expect(totals.order_total).toBe(1000);
  });
});
