export default defineAppConfig({
  // https://ui.nuxt.com/getting-started/theme#design-system
  icon: {
    size: "1rem",
  },
  ui: {
    colors: {
      primary: "blue",
      neutral: "slate",
    },
    card: {
      slots: {
        root: "bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm",
        body: "!gap-0 p-4 sm:p-6",
        header: "bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800",
      },
    },
    badge: {
      defaultVariants: {
        color: "neutral",
        variant: "outline",
      },
    },
    button: {
      slots: {
        base: "cursor-pointer",
      },
      defaultVariants: {
        // Set default button color to neutral
        color: "neutral",
        size: "lg",
      },
    },
    table: {
      slots: {
        root: "overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900",
        thead: "bg-slate-50 dark:bg-slate-950",
        th: "py-4 px-6 font-semibold text-slate-600 tracking-normal dark:text-slate-300",
        td: "py-4 px-6 text-slate-700 dark:text-slate-200",
        separator: "bg-slate-200 dark:bg-slate-800",
      },
    },
    select: {
      slots: {
        base: "cursor-pointer",
      },
      defaultVariants: {
        // Set default button color to neutral
        color: "neutral",
        size: "lg",
      },
    },
  },
});
