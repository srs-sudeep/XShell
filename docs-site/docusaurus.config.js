// @ts-check
const childProcess = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");
const { themes: prismThemes } = require("prism-react-renderer");

const repoRoot = path.resolve(__dirname, "..");

function hasReadableGitMetadata() {
  if (!fs.existsSync(path.join(repoRoot, ".git"))) {
    return false;
  }

  try {
    childProcess.execSync("git rev-parse --verify HEAD", {
      cwd: repoRoot,
      stdio: "ignore",
    });
    return true;
  } catch {
    return false;
  }
}

const hasGitMetadata = hasReadableGitMetadata();

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: "XShell",
  tagline: "A feature-rich cross-platform shell built in Python",
  favicon: "img/favicon.ico",
  url: "https://x-shell.vercel.app",
  baseUrl: "/",
  onBrokenLinks: "throw",
  markdown: {
    hooks: {
      onBrokenMarkdownLinks: "warn",
    },
  },

  i18n: {
    defaultLocale: "en",
    locales: ["en"],
  },

  presets: [
    [
      "classic",
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: require.resolve("./sidebars.js"),
          routeBasePath: "/docs",
          showLastUpdateTime: hasGitMetadata,
        },
        blog: false,
        theme: {
          customCss: require.resolve("./src/css/custom.css"),
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      image: "img/xshell-social.png",
      colorMode: {
        defaultMode: "dark",
        disableSwitch: false,
        respectPrefersColorScheme: true,
      },
      navbar: {
        title: "XShell",
        logo: {
          alt: "XShell Logo",
          src: "img/logo.svg",
        },
        items: [
          {
            type: "docSidebar",
            sidebarId: "docs",
            position: "left",
            label: "Docs",
          },
          {
            to: "/docs/commands",
            label: "Commands",
            position: "left",
          },
          {
            to: "/docs/plugins",
            label: "Plugins",
            position: "left",
          },
          {
            href: "https://github.com/srs-sudeep/XShell/releases",
            label: "Download",
            position: "right",
          },
          {
            href: "https://github.com/srs-sudeep/XShell",
            label: "GitHub",
            position: "right",
          },
          {
            href: "https://x-shell.vercel.app/",
            label: "Live Docs",
            position: "right",
          },
        ],
      },

      footer: {
        style: "dark",
        links: [
          {
            title: "Docs",
            items: [
              { label: "Getting Started", to: "/docs/getting-started" },
              { label: "Commands", to: "/docs/commands" },
              { label: "Plugins", to: "/docs/plugins" },
              { label: "Themes", to: "/docs/themes" },
            ],
          },
          {
            title: "Guides",
            items: [
              { label: "Writing Plugins", to: "/docs/plugins/writing-plugins" },
              { label: "Custom Themes", to: "/docs/themes/custom-themes" },
              { label: "Configuration", to: "/docs/configuration" },
              { label: "Building & Packaging", to: "/docs/building" },
            ],
          },
          {
            title: "More",
            items: [
              {
                label: "Download Releases",
                href: "https://github.com/srs-sudeep/XShell/releases",
              },
              { label: "GitHub", href: "https://github.com/srs-sudeep/XShell" },
              { label: "Live Docs", href: "https://x-shell.vercel.app/" },
              { label: "Changelog", to: "/docs/changelog" },
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} XShell Contributors. Built with Docusaurus.`,
      },

      prism: {
        theme: prismThemes.oneDark,
        darkTheme: prismThemes.oneDark,
        additionalLanguages: ["bash", "json", "python", "powershell"],
      },

      algolia: undefined,
    }),
};

module.exports = config;
