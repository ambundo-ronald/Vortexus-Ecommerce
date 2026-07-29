import {
  basketTaxStatuses,
  checkoutTaxTotal,
  normalizeCheckoutTotals,
  taxStatusLabel
} from "../../src/utils/checkoutTotals";

describe("checkoutTotals", () => {
  test("reads tax from the backend nested tax state", () => {
    expect(checkoutTaxTotal({ taxes: { total_tax: 160 } })).toBe(160);
    expect(checkoutTaxTotal({ tax_breakdown: { total_tax: 0 } })).toBe(0);
  });

  test("normalizes checkout totals without calculating product tax locally", () => {
    expect(
      normalizeCheckoutTotals({
        basket: { totals: { subtotal: 1000, currency: "KES" } },
        shipping: { totals: { shipping: 200, taxes: { total_tax: 160 }, order_total: 1360, currency: "KES" } }
      })
    ).toEqual(expect.objectContaining({
      subtotal: 1000,
      shipping: 200,
      tax: 160,
      order_total: 1360,
      currency: "KES"
    }));
  });

  test("formats supported product tax states", () => {
    expect(taxStatusLabel("taxable")).toBe("Taxable");
    expect(taxStatusLabel("tax_exempt")).toBe("Tax exempt");
    expect(taxStatusLabel("zero_rated")).toBe("Zero-rated");
  });

  test("collects tax states from backend line breakdown and product payloads", () => {
    const statuses = basketTaxStatuses({
      tax_breakdown: {
        line_breakdown: [{ tax_status: "tax_exempt" }]
      },
      lines: [{ product: { tax_status: "zero_rated" } }]
    });

    expect(statuses).toEqual(["Tax exempt", "Zero-rated"]);
  });
});
