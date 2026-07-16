/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#12172B",
        paper: "#F7F8FA",
        paperdim: "#EEF0F4",
        indigo: {
          DEFAULT: "#3B4FE0",
          dark: "#2C3BB0",
          light: "#E8EAFB",
        },
        sage: {
          DEFAULT: "#2F855A",
          light: "#E6F4EC",
        },
        amber: {
          DEFAULT: "#C67C1E",
          light: "#FBF0DF",
        },
        slate: {
          line: "#E2E5EC",
          soft: "#6B7280",
        },
      },
      fontFamily: {
        display: ["Fraunces", "ui-serif", "Georgia", "serif"],
        body: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(18, 23, 43, 0.04), 0 4px 16px rgba(18, 23, 43, 0.06)",
      },
    },
  },
  plugins: [],
};
