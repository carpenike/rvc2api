import React, { useEffect, useState } from "react";

interface LatestRelease {
  latest_version: string | null;
  error?: string | null;
  latest_release_info?: {
    tag_name?: string;
    html_url?: string;
    name?: string;
    body?: string;
    published_at?: string;
  } | null;
}

/**
 * Footer component for the application
 * - Semantic <footer> with ARIA role
 * - Responsive, theme-adaptive, accessible
 * - Shows version and update info
 */
const Footer: React.FC = () => {
  const [currentVersion, setCurrentVersion] = useState<string | null>(null);
  const [latest, setLatest] = useState<LatestRelease | null>(null);
  const [checking, setChecking] = useState(false);

  useEffect(() => {
    fetch("/api/status/server")
      .then((resp) => resp.json())
      .then((serverStatus) => {
        setCurrentVersion(serverStatus.version || null);
      });
    setChecking(true);
    fetch("/api/status/latest_release")
      .then((resp) => resp.json())
      .then((data: LatestRelease) => {
        setLatest(data);
        setChecking(false);
      })
      .catch(() => setChecking(false));
  }, []);

  let updateInfo: React.ReactNode = null;
  if (checking) {
    updateInfo = <span className="ml-2 text-yellow-500">Checking for updates…</span>;
  } else if (latest && currentVersion) {
    if (latest.latest_version && latest.latest_version !== currentVersion) {
      updateInfo = (
        <span className="ml-2 text-yellow-400">
          <a
            href={
              latest.latest_release_info?.html_url ||
              `https://github.com/carpenike/rvc2api/releases/tag/v${latest.latest_version}`
            }
            target="_blank"
            rel="noopener noreferrer"
            className="underline hover:text-yellow-300"
          >
            v{latest.latest_version} available
          </a>
        </span>
      );
    } else if (latest.latest_version === currentVersion) {
      updateInfo = <span className="ml-2 text-green-500">Up to date</span>;
    }
  }

  return (
    <footer
      className="hidden lg:flex bg-[var(--color-surface)] text-[var(--color-text)] text-xs p-4 justify-between items-center shadow-lg border-t border-[var(--color-border)]"
      role="contentinfo"
    >
      <span>
        rvc2api React UI
        {currentVersion && (
          <span className="ml-2 text-[color:var(--color-text-secondary)] opacity-70">v{currentVersion}</span>
        )}
        {updateInfo}
      </span>
      <span>© {new Date().getFullYear()}</span>
    </footer>
  );
};

export default Footer;
