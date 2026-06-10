jest.mock("../../src/utils/media", () => ({
  mediaUrl: (value) => value
}));

import { productImageList, productImageUrl } from "../../src/utils/productImages";

describe("product image helpers", () => {
  test("cache-busts product images with the product update timestamp", () => {
    const product = {
      thumbnail: "/media/products/pump.jpg",
      updated_at: "2026-06-08T09:30:00Z"
    };

    expect(productImageUrl(product)).toContain(
      "/media/products/pump.jpg?v=2026-06-08T09%3A30%3A00Z"
    );
  });

  test("does not duplicate the primary image in the gallery", () => {
    const product = {
      thumbnail: "/media/products/pump.jpg",
      images: [
        { src: "/media/products/pump.jpg" },
        { src: "/media/products/pump-side.jpg" }
      ],
      updated_at: "2026-06-08T09:30:00Z"
    };

    expect(productImageList(product)).toHaveLength(2);
  });
});
