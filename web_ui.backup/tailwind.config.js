/** @type {import("tailwindcss").Config} */

const config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  safelist: [
    {
      pattern:
        /^accent-(slate|gray|zinc|neutral|stone|red|rose|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink)$/,
      variants: ["hover", "focus"]
    }
  ],
  theme: {
    extend: {
      colors: {
        // Main color tokens (mapped to CSS variables from global.css)
        background: "var(--background)",
        foreground: "var(--foreground)",
        card: "var(--card)",
        "card-foreground": "var(--card-foreground)",
        popover: "var(--popover)",
        "popover-foreground": "var(--popover-foreground)",
        primary: "var(--primary)",
        "primary-foreground": "var(--primary-foreground)",
        secondary: "var(--secondary)",
        "secondary-foreground": "var(--secondary-foreground)",
        muted: "var(--muted)",
        "muted-foreground": "var(--muted-foreground)",
        accent: "var(--accent)",
        "accent-foreground": "var(--accent-foreground)",
        destructive: "var(--destructive)",
        border: "var(--border)",
        input: "var(--input)",
        ring: "var(--ring)",
        // Chart colors (optional)
        "chart-1": "var(--chart-1)",
        "chart-2": "var(--chart-2)",
        "chart-3": "var(--chart-3)",
        "chart-4": "var(--chart-4)",
        "chart-5": "var(--chart-5)",
        // Sidebar tokens
        sidebar: "var(--sidebar)",
        "sidebar-foreground": "var(--sidebar-foreground)",
        "sidebar-primary": "var(--sidebar-primary)",
        "sidebar-primary-foreground": "var(--sidebar-primary-foreground)",
        "sidebar-accent": "var(--sidebar-accent)",
        "sidebar-accent-foreground": "var(--sidebar-accent-foreground)",
        "sidebar-border": "var(--sidebar-border)",
        "sidebar-ring": "var(--sidebar-ring)",
      },
      borderRadius: {
        // These keys map to your CSS variables (radius helpers)
        sm: "var(--radius-sm)",
        DEFAULT: "var(--radius-md)",
        md: "var(--radius-md)",
        lg: "var(--radius-lg)",
        xl: "var(--radius-xl)",
      },
      fontFamily: {
        // Font families now defined in CSS @theme - keeping system fallback here
        sans: [
          "var(--font-sans)",
          "system-ui",
          "sans-serif",
        ],
        serif: [
          "var(--font-serif)",
          "Georgia",
          "serif",
        ],
        mono: [
          "var(--font-mono)",
          "ui-monospace",
          "monospace",
        ],
        display: [
          "var(--font-display)",
          "system-ui",
          "sans-serif",
        ],
        heading: [
          "var(--font-heading)",
          "system-ui",
          "sans-serif",
        ],
      },
    },
  },
};

export default config;
