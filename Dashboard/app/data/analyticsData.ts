export type AnalyticsKpi = {
  totalSessions: number;
  sessionDuration: string;
  pagesPerSession: number;
  bounceRate: number;
  trend: number;
};

export type AnalyticsAction = {
  label: string;
  sessions: number;
  width: string;
};

export type AnalyticsTraffic = {
  label: string;
  sessions: number;
  width: string;
};

export type AnalyticsData = {
  kpi: AnalyticsKpi;
  topLinks: AnalyticsAction[];
  topTraffic: AnalyticsTraffic[];
  charts?: {
    totalSessions: { date: string; desktop: number }[];
    sessionDuration: { date: string; desktop: number }[];
    pagesPerSession: { date: string; desktop: number }[];
    bounceRate: { date: string; bounce: number }[];
  };
};

export type AnalyticsDataset = Record<string, AnalyticsData>;

export const analyticsDataset: AnalyticsDataset = {
  'Last 7 days': {
    "kpi": {
      "totalSessions": 120,
      "sessionDuration": "2:10",
      "pagesPerSession": 1.8,
      "bounceRate": 44.2,
      "trend": 1.2
    },
    "topLinks": [
      { "label": "Add to Cart", "sessions": 30, "width": "90%" },
      { "label": "View Product Details", "sessions": 25, "width": "80%" },
      { "label": "Checkout", "sessions": 18, "width": "65%" },
      { "label": "Apply Discount Code", "sessions": 10, "width": "35%" },
      { "label": "Wishlist", "sessions": 8, "width": "28%" },
      { "label": "Share Product", "sessions": 6, "width": "20%" },
      { "label": "Track Order", "sessions": 4, "width": "15%" },
      { "label": "Contact Support", "sessions": 3, "width": "10%" },
      { "label": "Leave Review", "sessions": 2, "width": "8%" },
      { "label": "View Blog Post", "sessions": 7, "width": "25%" },
      { "label": "Sign Up for Newsletter", "sessions": 5, "width": "18%" },
      { "label": "Apply for Account", "sessions": 4, "width": "15%" }
    ],
    "topTraffic": [
      { "label": "/", "sessions": 40, "width": "95%" },
      { "label": "/products/smartphone-x", "sessions": 30, "width": "80%" },
      { "label": "/products/laptop-pro", "sessions": 20, "width": "70%" },
      { "label": "/products/wireless-earbuds", "sessions": 15, "width": "60%" },
      { "label": "/cart", "sessions": 12, "width": "50%" },
      { "label": "/checkout", "sessions": 8, "width": "35%" },
      { "label": "/account/orders", "sessions": 6, "width": "25%" },
      { "label": "/products/smartwatch", "sessions": 5, "width": "22%" },
      { "label": "/support", "sessions": 2, "width": "10%" },
      { "label": "/blog/latest-tech-trends", "sessions": 10, "width": "45%" },
      { "label": "/promotions/summer-sale", "sessions": 9, "width": "40%" },
      { "label": "/about-us", "sessions": 7, "width": "30%" }
    ]
  },
  'Last 30 days': {
    kpi: {
      totalSessions: 1069,
      sessionDuration: '2:20',
      pagesPerSession: 2.0,
      bounceRate: 43.0,
      trend: 1.8,
    },
    "topLinks": [
      { "label": "Add to Cart", "sessions": 30, "width": "90%" },
      { "label": "View Product Details", "sessions": 25, "width": "80%" },
      { "label": "Checkout", "sessions": 18, "width": "65%" },
      { "label": "Apply Discount Code", "sessions": 10, "width": "35%" },
      { "label": "Wishlist", "sessions": 8, "width": "28%" },
      { "label": "Share Product", "sessions": 6, "width": "20%" },
      { "label": "Track Order", "sessions": 4, "width": "15%" },
      { "label": "Contact Support", "sessions": 3, "width": "10%" },
      { "label": "Leave Review", "sessions": 2, "width": "8%" },
      { "label": "View Blog Post", "sessions": 7, "width": "25%" },
      { "label": "Sign Up for Newsletter", "sessions": 5, "width": "18%" },
      { "label": "Apply for Account", "sessions": 4, "width": "15%" }
    ],
    "topTraffic": [
      { "label": "/", "sessions": 40, "width": "95%" },
      { "label": "/products/smartphone-x", "sessions": 30, "width": "80%" },
      { "label": "/products/laptop-pro", "sessions": 20, "width": "70%" },
      { "label": "/products/wireless-earbuds", "sessions": 15, "width": "60%" },
      { "label": "/cart", "sessions": 12, "width": "50%" },
      { "label": "/checkout", "sessions": 8, "width": "35%" },
      { "label": "/account/orders", "sessions": 6, "width": "25%" },
      { "label": "/products/smartwatch", "sessions": 5, "width": "22%" },
      { "label": "/support", "sessions": 2, "width": "10%" },
      { "label": "/blog/latest-tech-trends", "sessions": 10, "width": "45%" },
      { "label": "/promotions/summer-sale", "sessions": 9, "width": "40%" },
      { "label": "/about-us", "sessions": 7, "width": "30%" }
    ],
    charts: {
      totalSessions: [
        { date: '2024-04-01', desktop: 222 },
        { date: '2024-04-02', desktop: 180 },
        { date: '2024-04-03', desktop: 167 },
        { date: '2024-04-04', desktop: 260 },
        { date: '2024-04-05', desktop: 240 },
      ],
      sessionDuration: [
        { date: '2024-04-01', desktop: 222 },
        { date: '2024-04-02', desktop: 180 },
        { date: '2024-04-03', desktop: 167 },
        { date: '2024-04-04', desktop: 260 },
        { date: '2024-04-05', desktop: 240 },
      ],
      pagesPerSession: [
        { date: '2024-04-01', desktop: 2.1 },
        { date: '2024-04-02', desktop: 1.8 },
        { date: '2024-04-03', desktop: 2.3 },
        { date: '2024-04-04', desktop: 2.0 },
        { date: '2024-04-05', desktop: 2.4 },
      ],
      bounceRate: [
        { date: '2024-04-01', bounce: 38 },
        { date: '2024-04-02', bounce: 41 },
        { date: '2024-04-03', bounce: 36 },
        { date: '2024-04-04', bounce: 33 },
        { date: '2024-04-05', bounce: 35 },
      ],
    },
  },
  'Last 90 days': {
    kpi: {
      totalSessions: 1420,
      sessionDuration: '2:32',
      pagesPerSession: 2.3,
      bounceRate: 41.1,
      trend: 3.1,
    },
    topLinks: [
      { label: 'Add to Cart', sessions: 340, width: '90%' },
      { label: 'View Product Details', sessions: 290, width: '80%' },
      { label: 'Checkout', sessions: 210, width: '65%' },
      { label: 'Apply Discount Code', sessions: 110, width: '35%' },
      { label: 'Wishlist', sessions: 90, width: '28%' },
      { label: 'Share Product', sessions: 70, width: '20%' },
      { label: 'Track Order', sessions: 55, width: '15%' },
      { label: 'Contact Support', sessions: 38, width: '10%' },
      { label: 'Leave Review', sessions: 30, width: '8%' },
    ],
    topTraffic: [
      { label: '/', sessions: 410, width: '95%' },
      { label: '/products/smartphone-x', sessions: 320, width: '80%' },
      { label: '/products/laptop-pro', sessions: 260, width: '70%' },
      { label: '/products/wireless-earbuds', sessions: 210, width: '60%' },
      { label: '/cart', sessions: 170, width: '50%' },
      { label: '/checkout', sessions: 120, width: '35%' },
      { label: '/account/orders', sessions: 90, width: '25%' },
      { label: '/products/smartwatch', sessions: 80, width: '22%' },
      { label: '/support', sessions: 45, width: '10%' },
    ],
  },
  'Total Sessions Chart': {
    kpi: {
      totalSessions: 222 + 180 + 167 + 260 + 240,
      sessionDuration: '2:20',
      pagesPerSession: 2.0,
      bounceRate: 43.0,
      trend: 1.8,
    },
    topLinks: [],
    topTraffic: [
      { label: '2024-04-01', sessions: 222, width: '45%' },
      { label: '2024-04-02', sessions: 180, width: '36%' },
      { label: '2024-04-03', sessions: 167, width: '34%' },
      { label: '2024-04-04', sessions: 260, width: '53%' },
      { label: '2024-04-05', sessions: 240, width: '49%' },
    ],
  },
};
