/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#020817",
        foreground: "#f8fafc",
        primary: {
          DEFAULT: "#0ea5e9",
          hover: "#0284c7",
        },
        secondary: {
          DEFAULT: "#1e293b",
          hover: "#334155",
        },
        risk: {
          low: "#10b981",    // tailwind green-500
          medium: "#eab308", // tailwind yellow-500
          high: "#f97316",   // tailwind orange-500
          critical: "#ef4444",// tailwind red-500
        },
        gov: {
          navy: "#1a233a",
          dark: "#0b101e",
          blue: "#2563eb",
          card: "#111827",
        }
      }
    },
  },
  plugins: [],
}
