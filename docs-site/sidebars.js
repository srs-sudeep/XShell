/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  docs: [
    {
      type: "category",
      label: "Overview",
      collapsed: false,
      items: ["intro", "getting-started", "installation", "demo-media"],
    },
    {
      type: "category",
      label: "Commands",
      collapsed: false,
      link: { type: "doc", id: "commands/index" },
      items: [
        "commands/navigation",
        "commands/files",
        "commands/shell",
        "commands/builtin-plugins",
      ],
    },
    {
      type: "category",
      label: "Themes",
      link: { type: "doc", id: "themes/index" },
      items: ["themes/custom-themes"],
    },
    {
      type: "category",
      label: "Plugins",
      link: { type: "doc", id: "plugins/index" },
      items: ["plugins/builtin", "plugins/writing-plugins"],
    },
    "web-terminal",
    "configuration",
    "building",
    "changelog",
  ],
};

module.exports = sidebars;
