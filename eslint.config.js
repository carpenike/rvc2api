// Root ESLint Flat Config for rvc2api monorepo
import webUiConfig from "./web_ui/eslint.config.js";

export default [
  // Global ignores (covers all build/output/generated files)
  {
    ignores: [
      "**/node_modules/**",
      "**/dist/**",
      "**/dist-ssr/**",
      "**/.vite/**",
      "**/.vite-temp/**",
      "**/build/**",
      "**/site/**", // MkDocs and documentation output
      "**/docs/_build/**", // Sphinx or other doc builds
      "**/*.tsbuildinfo",
      "**/*.log",
      "**/.cache/**",
      "**/assets/javascripts/workers/*.min.js", // Minified/generated JS (e.g., search workers)
      "**/CNAME",
      "**/objects.inv",
      "**/sitemap.xml*",
      "**/index.html",
      "**/404.html"
    ]
  },
  ...webUiConfig
];
