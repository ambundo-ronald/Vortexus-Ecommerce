import type { Order } from "~/components/Cards/LatestOrdersCard.vue";

export const RevenueData = [
  { month: "July 2023", total: 180 },
  { month: "August 2023", total: 195 },
  { month: "September 2023", total: 210 },
  { month: "October 2023", total: 225 },
  { month: "November 2023", total: 240 },
  { month: "December 2023", total: 260 },
  { month: "January 2024", total: 205 },
  { month: "February 2024", total: 220 },
  { month: "March 2024", total: 235 },
  { month: "April 2024", total: 250 },
  { month: "May 2024", total: 265 },
  { month: "June 2024", total: 280 },
  { month: "July 2024", total: 250 },
  { month: "August 2024", total: 310 },
  { month: "September 2024", total: 360 },
  { month: "October 2024", total: 280 },
  { month: "November 2024", total: 330 },
  { month: "December 2024", total: 390 },
  { month: "January 2025", total: 266 },
  { month: "February 2025", total: 505 },
  { month: "March 2025", total: 357 },
  { month: "April 2025", total: 263 },
  { month: "May 2025", total: 339 },
  { month: "June 2025", total: 354 },
];

export const RevenueCategoriesMultiple = {
  total: { name: "Total", color: "#3b82f6" },
};

export const xFormatter = (i: number): string => `${RevenueData[i]?.month}`;
export const yFormatter = (i: number) => `${i}`;

export const orders: Order[] = [
  { id: 1001, customer: "Alice", date: "2025-06-18", total: 120.5, status: "Paid" },
  { id: 1002, customer: "Bob", date: "2025-06-17", total: 89.99, status: "Pending" },
  { id: 1003, customer: "Charlie", date: "2025-06-16", total: 45.0, status: "Paid" },
  { id: 1004, customer: "Diana", date: "2025-06-15", total: 210.0, status: "Failed" },
  { id: 1005, customer: "Eve", date: "2025-06-14", total: 67.25, status: "Paid" },
];

export const DonutData = [
  { color: "#3b82f6", name: "Laptops", value: 38 },
  { color: "#a855f7", name: "Smartphones", value: 27 },
  { color: "#22c55e", name: "PC Components", value: 18 },
  { color: "#f59e42", name: "Monitors", value: 9 },
];

export const products = [
  { id: 1, name: 'MacBook Pro 16"', category: 'Laptops', stock: 8, image: '/images/products/iphone.png' },
  { id: 2, name: 'iPhone 15 Pro', category: 'Smartphones', stock: 0, image: '/images/products/iphone.webp' },
  { id: 3, name: 'Dell UltraSharp 27', category: 'Monitors', stock: 15, image: '/images/products/dell.webp' },
  { id: 4, name: 'Logitech MX Master 3S', category: 'Accessories', stock: 4, image: '/images/products/mx-master.webp' },
];

export const ReturnsData = {
  chartData: [
    { date: 'Jan 23', returns: 45 },
    { date: 'Feb 23', returns: 38 },
    { date: 'Mar 23', returns: 52 },
    { date: 'Apr 23', returns: 41 },
    { date: 'May 23', returns: 36 },
    { date: 'Jun 23', returns: 29 },
    { date: 'Jul 23', returns: 33 },
    { date: 'Aug 23', returns: 27 },
    { date: 'Sep 23', returns: 31 },
    { date: 'Oct 23', returns: 25 },
    { date: 'Nov 23', returns: 22 },
    { date: 'Dec 23', returns: 19 },
  ],
  categories: {
    returns: { name: 'Returns', color: '#a1a1aa' },
  },
};

export const RevenueDataCard = {
  chartData: [
    {
      date: 'Jan 23',
      subscriptions: 2890,
      downloads: 2338,
    },
    {
      date: 'Feb 23',
      subscriptions: 2756,
      downloads: 2103,
    },
    {
      date: 'Mar 23',
      subscriptions: 3322,
      downloads: 2194,
    },
    {
      date: 'Apr 23',
      subscriptions: 3470,
      downloads: 2108,
    },
    {
      date: 'May 23',
      subscriptions: 3475,
      downloads: 1812,
    },
    {
      date: 'Jun 23',
      subscriptions: 3129,
      downloads: 1726,
    },
    {
      date: 'Jul 23',
      subscriptions: 3490,
      downloads: 1982,
    },
    {
      date: 'Aug 23',
      subscriptions: 2903,
      downloads: 2012,
    },
    {
      date: 'Sep 23',
      subscriptions: 2643,
      downloads: 2342,
    },
    {
      date: 'Oct 23',
      subscriptions: 2837,
      downloads: 2473,
    },
    {
      date: 'Nov 23',
      subscriptions: 2954,
      downloads: 3848,
    },
    {
      date: 'Dec 23',
      subscriptions: 3239,
      downloads: 3736,
    },
  ],
  categories: {
    subscriptions: { name: 'Subscriptions', color: '#3b82f6' },
  },
};

export const SalesData = {
  chartData: [
    {
      date: 'Jan 23',
      sales: 1245,
    },
    {
      date: 'Feb 23',
      sales: 1390,
    },
    {
      date: 'Mar 23',
      sales: 1512,
    },
    {
      date: 'Apr 23',
      sales: 1620,
    },
    {
      date: 'May 23',
      sales: 1750,
    },
    {
      date: 'Jun 23',
      sales: 1688,
    },
    {
      date: 'Jul 23',
      sales: 1823,
    },
    {
      date: 'Aug 23',
      sales: 1940,
    },
    {
      date: 'Sep 23',
      sales: 2012,
    },
    {
      date: 'Oct 23',
      sales: 2105,
    },
    {
      date: 'Nov 23',
      sales: 2250,
    },
    {
      date: 'Dec 23',
      sales: 2398,
    },
  ],
  categories: {
    sales: { name: 'Sales', color: '#3b82f6' },
  },
};
