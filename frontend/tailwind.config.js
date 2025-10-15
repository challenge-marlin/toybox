/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/**/*.{js,ts,jsx,tsx,mdx}"
  ],
  theme: {
    extend: {
      colors: {
        steam: {
          brown: {
            50: "#F6F0EA",
            100: "#EADFCC",
            200: "#D6BE9D",
            300: "#C09A6B",
            400: "#A87945",
            500: "#8C5C2E",
            600: "#6F4622",
            700: "#58371B",
            800: "#3D2411",
            900: "#2A190C"
          },
          gold: {
            50: "#FFF9E6",
            100: "#FFF1BF",
            200: "#FFE480",
            300: "#FFD74A",
            400: "#FFC626",
            500: "#E0A800",
            600: "#B88700",
            700: "#8F6900",
            800: "#6B4E00",
            900: "#4D3700"
          },
          iron: {
            50: "#F2F3F5",
            100: "#E2E6EA",
            200: "#C8CED6",
            300: "#A6AFBD",
            400: "#8591A2",
            500: "#697483",
            600: "#515A66",
            700: "#3E4550",
            800: "#2C3139",
            900: "#1F232A"
          }
        }
      }
    }
  },
  plugins: []
};
