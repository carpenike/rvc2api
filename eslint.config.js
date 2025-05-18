// Root ESLint Flat Config for rvc2api monorepo
import webUiConfig from "./web_ui/eslint.config.js";

export default [
  // Global ignores (optional, can be extended)
  {
    ignores: ["**/node_modules/**", "**/dist/**", "**/build/**"]
  },
  ...webUiConfig
];
