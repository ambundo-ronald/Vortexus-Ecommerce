import { groupMarketingBlocks, sortMarketingBlocks } from "../../src/utils/marketingBlocks";

describe("marketing block utilities", () => {
  test("groups every supported placement and sorts by configured order", () => {
    const grouped = groupMarketingBlocks([
      { id: 4, placement: "brand_strip", sort_order: 3 },
      { id: 2, placement: "home_hero", sort_order: 2 },
      { id: 1, placement: "home_hero", sort_order: 1 },
      { id: 8, placement: "top_category", sort_order: 0 }
    ]);

    expect(grouped.home_hero.map((block) => block.id)).toEqual([1, 2]);
    expect(grouped.brand_strip.map((block) => block.id)).toEqual([4]);
    expect(grouped.top_category.map((block) => block.id)).toEqual([8]);
    expect(grouped.announcement).toEqual([]);
  });

  test("uses grouped API data when it is available", () => {
    const grouped = groupMarketingBlocks(
      [{ id: 99, placement: "featured", sort_order: 0 }],
      { featured: [{ id: 3, sort_order: 2 }, { id: 2, sort_order: 1 }] }
    );

    expect(grouped.featured.map((block) => block.id)).toEqual([2, 3]);
  });

  test("falls back to flat results when the grouped payload is empty", () => {
    const grouped = groupMarketingBlocks(
      [{ id: 7, placement: "announcement", sort_order: 0 }],
      {}
    );

    expect(grouped.announcement.map((block) => block.id)).toEqual([7]);
  });

  test("does not mutate the source array while sorting", () => {
    const source = [{ id: 2, sort_order: 2 }, { id: 1, sort_order: 1 }];

    expect(sortMarketingBlocks(source).map((block) => block.id)).toEqual([1, 2]);
    expect(source.map((block) => block.id)).toEqual([2, 1]);
  });
});
