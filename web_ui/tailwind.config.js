/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      borderRadius: {
        xl: "1rem",
        "2xl": "1.5rem",
        "3xl": "2rem"
      },
      colors: {
        "rv-primary": "#3B82F6",
        "rv-secondary": "#10B981",
        "rv-accent": "#8B5CF6",
        "rv-background": "#1E293B",
        "rv-surface": "#334155",
        "rv-text": "#F8FAFC",
        "rv-error": "#EF4444",
        "rv-warning": "#F59E0B",
        "rv-success": "#10B981"
      }
    }
  },
  plugins: []
};
