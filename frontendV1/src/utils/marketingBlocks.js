export const MARKETING_PLACEMENTS = Object.freeze([
  "home_hero",
  "announcement",
  "promo_banner",
  "featured",
  "brand_strip",
  "top_category"
]);

export function groupMarketingBlocks(blocks = [], apiGroups = null) {
  const hasGroupedResults =
    apiGroups &&
    typeof apiGroups === "object" &&
    MARKETING_PLACEMENTS.some((placement) => Array.isArray(apiGroups[placement]));

  if (hasGroupedResults) {
    return MARKETING_PLACEMENTS.reduce((groups, placement) => {
      groups[placement] = sortMarketingBlocks(apiGroups[placement]);
      return groups;
    }, {});
  }

  const groups = MARKETING_PLACEMENTS.reduce((result, placement) => {
    result[placement] = [];
    return result;
  }, {});

  blocks.forEach((block) => {
    const placement = MARKETING_PLACEMENTS.includes(block?.placement) ? block.placement : "featured";
    groups[placement].push(block);
  });

  Object.keys(groups).forEach((placement) => {
    groups[placement] = sortMarketingBlocks(groups[placement]);
  });

  return groups;
}

export function sortMarketingBlocks(blocks = []) {
  return [...(Array.isArray(blocks) ? blocks : [])].sort((left, right) => {
    const orderDifference = Number(left?.sort_order || 0) - Number(right?.sort_order || 0);
    if (orderDifference) return orderDifference;
    return Number(left?.id || 0) - Number(right?.id || 0);
  });
}
