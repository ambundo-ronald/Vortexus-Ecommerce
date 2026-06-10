import {
  productBrand,
  productCategory,
  productRating,
  stockTone
} from "../../src/utils/productDisplay";

describe("product display helpers", () => {
  test("uses nested product metadata consistently", () => {
    const line = {
      product: {
        brand: "Hydramem",
        categories: [{ name: "RO Machines" }],
        rating: 4.5,
        review_count: 8
      }
    };

    expect(productBrand(line)).toBe("Hydramem");
    expect(productCategory(line)).toBe("RO Machines");
    expect(productRating(line)).toEqual({
      rating: 4.5,
      reviewCount: 8,
      hasRating: true
    });
  });

  test("prefers explicit unavailable state over positive stock", () => {
    expect(stockTone({
      stock_count: 9,
      availability: { is_available_to_buy: false }
    })).toEqual({
      tone: "warning",
      label: "Sold out",
      count: 0,
      isAvailable: false
    });
  });

  test("shows the available stock count", () => {
    expect(stockTone({ num_in_stock: 6, in_stock: true })).toEqual({
      tone: "success",
      label: "In stock: 6",
      count: 6,
      isAvailable: true
    });
  });
});
