export interface NavItem {
  label: string
  icon: string
  to: string
  highlight?: boolean
}

export interface NavSection {
  label: string
  items: NavItem[]
}

export const navSections: NavSection[] = [
  {
    label: 'Overview',
    items: [
      {
        label: 'Overview',
        icon: 'i-lucide-home',
        to: '/',
      },
      {
        label: 'Analytics',
        icon: 'i-lucide-activity',
        to: '/analytics',
      },
    ],
  },
  {
    label: 'Catalog',
    items: [
      {
        label: 'Products',
        icon: 'i-lucide-box',
        to: '/products',
      },
      {
        label: 'Categories',
        icon: 'i-lucide-folder-tree',
        to: '/catalog/categories',
      },
      {
        label: 'Product Types',
        icon: 'i-lucide-boxes',
        to: '/catalog/product-types',
      },
      {
        label: 'Attributes',
        icon: 'i-lucide-list-plus',
        to: '/catalog/attributes',
      },
      {
        label: 'Options',
        icon: 'i-lucide-settings-2',
        to: '/catalog/options',
      },
      {
        label: 'Stock Alerts',
        icon: 'i-lucide-bell-ring',
        to: '/catalog/stock-alerts',
      },
      {
        label: 'Reviews',
        icon: 'i-lucide-message-square-text',
        to: '/reviews',
      },
    ],
  },
  {
    label: 'Promotions',
    items: [
      {
        label: 'Offers',
        icon: 'i-lucide-badge-percent',
        to: '/promotions/offers',
      },
      {
        label: 'Vouchers',
        icon: 'i-lucide-ticket-percent',
        to: '/promotions/vouchers',
      },
      {
        label: 'Ranges',
        icon: 'i-lucide-layers-3',
        to: '/promotions/ranges',
      },
      {
        label: 'Campaigns',
        icon: 'i-lucide-megaphone',
        to: '/campaigns',
      },
    ],
  },
  {
    label: 'Operations',
    items: [
      {
        label: 'Orders',
        icon: 'i-lucide-receipt',
        to: '/orders',
      },
      {
        label: 'Users',
        icon: 'i-lucide-user',
        to: '/users',
      },
      {
        label: 'Partners',
        icon: 'i-lucide-handshake',
        to: '/partners',
      },
      {
        label: 'Suppliers',
        icon: 'i-lucide-store',
        to: '/suppliers',
      },
      {
        label: 'Shipping',
        icon: 'i-lucide-truck',
        to: '/shipping',
      },
      {
        label: 'Reports',
        icon: 'i-lucide-file-chart-column',
        to: '/reports',
      },
      {
        label: 'Audit Logs',
        icon: 'i-lucide-list-checks',
        to: '/audit-logs',
      },
      {
        label: 'Email Logs',
        icon: 'i-lucide-mail-search',
        to: '/email-logs',
      },
      {
        label: 'Payment Logs',
        icon: 'i-lucide-credit-card',
        to: '/payment-logs',
      },
      {
        label: 'Email Suppressions',
        icon: 'i-lucide-mail-x',
        to: '/email-suppressions',
      },
    ],
  },
  {
    label: 'Content',
    items: [
      {
        label: 'Media',
        icon: 'i-lucide-image',
        to: '/media',
      },
      {
        label: 'Pages',
        icon: 'i-lucide-files',
        to: '/content/pages',
      },
      {
        label: 'Marketing Blocks',
        icon: 'i-lucide-panels-top-left',
        to: '/content/marketing-blocks',
      },
      {
        label: 'Communications',
        icon: 'i-lucide-send',
        to: '/content/communications',
      },
      {
        label: 'Email Templates',
        icon: 'i-lucide-mail-plus',
        to: '/content/email-templates',
      },
    ],
  },
  {
    label: 'Settings',
    items: [
      {
        label: 'Integrations',
        icon: 'i-lucide-plug',
        to: '/integrations',
      },
      {
        label: 'Settings',
        icon: 'i-lucide-settings',
        to: '/settings',
      },
    ],
  },
]

export const mainNav = navSections.flatMap(section => section.items)

export const supportNav = [
  {
    label: "Support",
    icon: "i-lucide-message-circle",
    to: "/support",
    highlight: true,
  },
];

export const settingsNav = navSections.find(section => section.label === 'Settings')?.items || []
