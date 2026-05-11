import clsx from "clsx";
import styles from "./styles.module.css";

const features = [
  {
    icon: "🖥️",
    title: "Cross-Platform",
    description:
      "Runs identically on Windows, macOS, and Linux. One shell, every machine.",
  },
  {
    icon: "🎨",
    title: "5 Built-in Themes",
    description:
      'catppuccin, github-dark, gruvbox, onedark, tokyo-night. Switch live with "theme set <name>" and inspect with "theme info <name>".',
  },
  {
    icon: "🔌",
    title: "Plugin System",
    description:
      'Bundled plugins (git, sysinfo, calc) plus user and project-local plugins. Use "plugin available" and "plugin info" for discovery.',
  },
  {
    icon: "🔤",
    title: "Autocorrect",
    description:
      'Levenshtein-based typo detection. Type "gti" and XShell suggests "git" before giving up.',
  },
  {
    icon: "⌨️",
    title: "Smart Completion",
    description:
      "Tab-complete commands, files, directories, aliases, and plugin commands. Ctrl+R reverse-history search.",
  },
  {
    icon: "🌐",
    title: "Web Terminal",
    description:
      'Run "python main.py --web" to open a full-featured browser terminal with ANSI colours and a theme switcher. Video: youtu.be/LNP0p5zTUro',
  },
  {
    icon: "⛓️",
    title: "Full Pipeline Support",
    description:
      "Pipes, redirects, &&, ||, ;, background jobs — the complete Unix pipeline model on all platforms.",
  },
  {
    icon: "🔢",
    title: "Built-in Calculator",
    description:
      '"calc sqrt(144)", "convert 100 km mi", "convert 37 c f" — maths and unit conversion without leaving the shell.',
  },
  {
    icon: "📦",
    title: "Standalone Builds",
    description:
      '"python build.py" packages XShell into a single exe/binary via PyInstaller. No Python installation needed to run.',
  },
];

function Feature({ icon, title, description }) {
  return (
    <div className={clsx("col col--4", styles.feature)}>
      <div className="text--center">
        <span className="feature__icon">{icon}</span>
      </div>
      <div className="text--center padding-horiz--md">
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures() {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {features.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
