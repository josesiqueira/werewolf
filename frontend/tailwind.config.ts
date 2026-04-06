import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Background palette
        bg: {
          void: "var(--color-bg-void)",
          primary: "var(--color-bg-primary)",
          secondary: "var(--color-bg-secondary)",
          surface: "var(--color-bg-surface)",
          elevated: "var(--color-bg-elevated)",
          overlay: "var(--color-bg-overlay)",
        },
        // Text
        text: {
          primary: "var(--color-text-primary)",
          secondary: "var(--color-text-secondary)",
          muted: "var(--color-text-muted)",
          inverse: "var(--color-text-inverse)",
        },
        // Borders
        border: {
          subtle: "var(--color-border-subtle)",
          default: "var(--color-border-default)",
          strong: "var(--color-border-strong)",
        },
        // Day mode
        day: {
          sky: "var(--color-day-sky)",
          mist: "var(--color-day-mist)",
          warmth: "var(--color-day-warmth)",
          light: "var(--color-day-light)",
        },
        // Night mode
        night: {
          deep: "var(--color-night-deep)",
          sky: "var(--color-night-sky)",
          moon: "var(--color-night-moon)",
          eerie: "var(--color-night-eerie)",
        },
        // Profile colors
        ethos: {
          DEFAULT: "var(--color-ethos)",
          light: "var(--color-ethos-light)",
          dark: "var(--color-ethos-dark)",
        },
        pathos: {
          DEFAULT: "var(--color-pathos)",
          light: "var(--color-pathos-light)",
          dark: "var(--color-pathos-dark)",
        },
        logos: {
          DEFAULT: "var(--color-logos)",
          light: "var(--color-logos-light)",
          dark: "var(--color-logos-dark)",
        },
        authority: {
          DEFAULT: "var(--color-authority)",
          light: "var(--color-authority-light)",
          dark: "var(--color-authority-dark)",
        },
        reciprocity: {
          DEFAULT: "var(--color-reciprocity)",
          light: "var(--color-reciprocity-light)",
          dark: "var(--color-reciprocity-dark)",
        },
        scarcity: {
          DEFAULT: "var(--color-scarcity)",
          light: "var(--color-scarcity-light)",
          dark: "var(--color-scarcity-dark)",
        },
        baseline: {
          DEFAULT: "var(--color-baseline)",
          light: "var(--color-baseline-light)",
          dark: "var(--color-baseline-dark)",
        },
        // Semantic
        alive: "var(--color-alive)",
        dead: "var(--color-dead)",
        eliminated: "var(--color-eliminated)",
        werewolf: "var(--color-werewolf)",
        villager: "var(--color-villager)",
        seer: "var(--color-seer)",
        doctor: "var(--color-doctor)",
        mayor: "var(--color-mayor)",
        warning: "var(--color-warning)",
        error: "var(--color-error)",
        success: "var(--color-success)",
        info: "var(--color-info)",
        // Bid heat
        bid: {
          0: "var(--color-bid-0)",
          1: "var(--color-bid-1)",
          2: "var(--color-bid-2)",
          3: "var(--color-bid-3)",
          4: "var(--color-bid-4)",
        },
      },
      fontFamily: {
        display: ["Cinzel", "Palatino Linotype", "Georgia", "serif"],
        body: ["Nunito Sans", "Segoe UI", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "Consolas", "monospace"],
      },
      fontSize: {
        "2xs": "var(--font-size-2xs)",
        xs: "var(--font-size-xs)",
        sm: "var(--font-size-sm)",
        base: "var(--font-size-base)",
        lg: "var(--font-size-lg)",
        xl: "var(--font-size-xl)",
        "2xl": "var(--font-size-2xl)",
        "3xl": "var(--font-size-3xl)",
        "4xl": "var(--font-size-4xl)",
        hero: "var(--font-size-hero)",
      },
      borderRadius: {
        xs: "var(--radius-xs)",
        sm: "var(--radius-sm)",
        md: "var(--radius-md)",
        lg: "var(--radius-lg)",
        xl: "var(--radius-xl)",
        "2xl": "var(--radius-2xl)",
        full: "var(--radius-full)",
      },
      boxShadow: {
        sm: "var(--shadow-sm)",
        md: "var(--shadow-md)",
        lg: "var(--shadow-lg)",
        xl: "var(--shadow-xl)",
        "glow-moon": "var(--glow-moon)",
        "glow-fire": "var(--glow-fire)",
        "glow-eerie": "var(--glow-eerie)",
        "glow-elimination": "var(--glow-elimination)",
      },
      spacing: {
        "0.5": "var(--space-0-5)",
        "1": "var(--space-1)",
        "1.5": "var(--space-1-5)",
        "2": "var(--space-2)",
        "3": "var(--space-3)",
        "4": "var(--space-4)",
        "5": "var(--space-5)",
        "6": "var(--space-6)",
        "8": "var(--space-8)",
        "10": "var(--space-10)",
        "12": "var(--space-12)",
        "16": "var(--space-16)",
        "20": "var(--space-20)",
        "24": "var(--space-24)",
        "32": "var(--space-32)",
      },
      transitionDuration: {
        instant: "100ms",
        fast: "150ms",
        base: "250ms",
        slow: "400ms",
        dramatic: "800ms",
        phase: "1200ms",
      },
      zIndex: {
        base: "0",
        surface: "10",
        overlay: "20",
        modal: "30",
        tooltip: "40",
        navigation: "50",
      },
      maxWidth: {
        content: "var(--content-max-width)",
      },
      width: {
        sidebar: "var(--sidebar-width)",
        inspector: "var(--inspector-panel-width)",
      },
      height: {
        nav: "var(--nav-height)",
      },
      backdropBlur: {
        glass: "var(--glass-blur)",
      },
    },
  },
  plugins: [],
};
export default config;
