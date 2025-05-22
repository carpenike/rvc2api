/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      borderRadius: {
        xl: "0.75rem",
        "2xl": "1rem",
        "3xl": "1.5rem"
      },
      width: {
        "full-viewport": "100vw"
      },
      height: {
        "full-viewport": "100vh"
      },
      fontSize: {
        // Keep Tailwind defaults but add our custom xs size
        "xs": "0.75rem",
        "sm": "0.875rem",
        "base": "1rem",
        "lg": "1.125rem",
        "xl": "1.25rem",
        "2xl": "1.5rem",
        "3xl": "1.875rem",
        "4xl": "2.25rem",
        "5xl": "3rem"
      },
      colors: {
        // Default theme (dark blue)
        "rv-primary": "var(--rv-primary, #3B82F6)",
        "rv-secondary": "var(--rv-secondary, #10B981)",
        "rv-accent": "var(--rv-accent, #8B5CF6)",
        "rv-background": "var(--rv-background, #1E293B)",
        "rv-surface": "var(--rv-surface, #334155)",
        "rv-text": "var(--rv-text, #F8FAFC)",
        "rv-error": "var(--rv-error, #EF4444)",
        "rv-warning": "var(--rv-warning, #F59E0B)",
        "rv-success": "var(--rv-success, #10B981)"
      },
      spacing: {
        // Add custom spacing only, don't override Tailwind defaults
        "2.5": "0.625rem",
        "3.5": "0.875rem"
      }
    }
  },
  plugins: []
};
