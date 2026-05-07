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
        root: "bg-white border border-slate-200 shadow-sm",
        body: "!gap-0 p-4 sm:p-6",
        header: "bg-white border-b border-slate-200",
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
        root: "overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm",
        thead: "bg-slate-50",
        th: "py-4 px-6 font-semibold text-slate-600 tracking-normal",
        td: "py-4 px-6 text-slate-700",
        separator: "bg-slate-200",
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
