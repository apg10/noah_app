/* Shared Tailwind config for Noah HTML screens. Load this after the CDN script. */

tailwind.config = {
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        primary: "#59f20d",
        "background-light": "#f6f8f5",
        "background-dark": "#162210",
      },
      fontFamily: {
        display: ["Inter", "sans-serif"],
      },
      borderRadius: {
        DEFAULT: "0.5rem",
        lg: "1rem",
        xl: "1.5rem",
        full: "9999px",
      },
    },
  },
};
