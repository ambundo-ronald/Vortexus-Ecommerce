export default defineAppConfig({
  // https://ui.nuxt.com/getting-started/theme#design-system
  icon: {
    size: "1rem",
  },
  ui: {
    colors: {
      primary: "emerald",
      neutral: "neutral",
    },
    card: {
      slots: {
        body: "!gap-0 p-4 sm:p-6 !bg-elevated/20",
        header: "bg-muted dark:bg-elevated/20",
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
        root: "bg-default dark:bg-elevated/20 rounded-lg border border-default",
        thead: "[&>tr]:after:bg-(--ui-border)",
        th: "py-4 px-6 font-medium text-toned tracking-tight",
        td: "py-4 px-6 text-toned dark:text-muted",
        separator: 'bg-border'
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
