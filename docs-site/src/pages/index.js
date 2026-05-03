import Link from "@docusaurus/Link";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import HomepageFeatures from "@site/src/components/HomepageFeatures";
import Layout from "@theme/Layout";
import clsx from "clsx";
import styles from "./index.module.css";

function HeroBanner() {
  const { siteConfig } = useDocusaurusContext();
  return (
    <header className={clsx("hero hero--primary", styles.heroBanner)}>
      <div className="container">
        <pre className={styles.asciiLogo}>{`
  __  __ _____  _          _ _
 \\ \\/ // ____|| |        | | |
  >  <| (___  | |__   ___| | |
 / /\\ \\\\___ \\ | '_ \\ / _ \\ | |
/ ____ \\___) || | | |  __/ | |
/_/    \\_\\____/ |_| |_|\\___|_|_|`}</pre>
        <p className="hero__subtitle">{siteConfig.tagline}</p>
        <div className={styles.buttons}>
          <Link
            className="button button--primary button--lg"
            to="/docs/getting-started"
          >
            Get Started →
          </Link>
          <Link
            className="button button--secondary button--lg margin-left--md"
            to="/docs/commands"
          >
            Commands
          </Link>
          <Link
            className="button button--primary button--lg"
            to="https://github.com/srs-sudeep/XShell/releases"
          >
            Download
          </Link>
        </div>
        <div className={styles.quickInstall}>
          <code>pip install -r requirements.txt &amp;&amp; python main.py</code>
        </div>
      </div>
    </header>
  );
}

export default function Home() {
  return (
    <Layout description="A feature-rich cross-platform shell built in Python">
      <HeroBanner />
      <main>
        <HomepageFeatures />
      </main>
    </Layout>
  );
}
