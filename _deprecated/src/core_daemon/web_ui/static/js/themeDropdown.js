// themeDropdown.js - Custom theme dropdown logic for rvc2api UI
// Exports: initThemeDropdown()

const THEME_LABELS = {
  default: "Default Theme",
  dark: "Dark Theme",
  light: "Light Theme",
  "catppuccin-mocha": "Catppuccin Mocha",
  "catppuccin-latte": "Catppuccin Latte",
  "nord-dark": "Nord Dark",
  "nord-light": "Nord Light",
  "gruvbox-dark": "Gruvbox Dark",
  "gruvbox-light": "Gruvbox Light",
};

export function initThemeDropdown(applyTheme, SELECTED_THEME_KEY) {
  const themeDropdownButton = document.getElementById("themeDropdownButton");
  const themeDropdownMenu = document.getElementById("themeDropdownMenu");
  const themeDropdownLabel = document.getElementById("themeDropdownLabel");
  if (!themeDropdownButton || !themeDropdownMenu || !themeDropdownLabel) return;

  function setThemeDropdownLabel(theme) {
    themeDropdownLabel.textContent = THEME_LABELS[theme] || "Theme";
  }
  function closeThemeDropdown() {
    themeDropdownMenu.hidden = true;
    themeDropdownButton.setAttribute("aria-expanded", "false");
  }
  function openThemeDropdown() {
    themeDropdownMenu.hidden = false;
    themeDropdownButton.setAttribute("aria-expanded", "true");
    // Focus first item
    const first = themeDropdownMenu.querySelector("li");
    if (first) first.focus();
  }
  themeDropdownButton.addEventListener("click", (e) => {
    e.stopPropagation();
    if (themeDropdownMenu.hidden) {
      openThemeDropdown();
    } else {
      closeThemeDropdown();
    }
  });
  themeDropdownButton.addEventListener("keydown", (e) => {
    if (e.key === "ArrowDown" || e.key === "Enter" || e.key === " ") {
      openThemeDropdown();
      e.preventDefault();
    }
  });
  themeDropdownMenu.addEventListener("keydown", (e) => {
    const items = Array.from(themeDropdownMenu.querySelectorAll("li"));
    let idx = items.indexOf(document.activeElement);
    if (e.key === "ArrowDown") {
      if (idx < items.length - 1) items[idx + 1].focus();
      e.preventDefault();
    } else if (e.key === "ArrowUp") {
      if (idx > 0) items[idx - 1].focus();
      e.preventDefault();
    } else if (e.key === "Escape") {
      closeThemeDropdown();
      themeDropdownButton.focus();
    } else if (e.key === "Enter" || e.key === " ") {
      if (idx >= 0) items[idx].click();
    }
  });
  themeDropdownMenu.querySelectorAll("li").forEach((li) => {
    li.tabIndex = 0;
    li.addEventListener("click", () => {
      const value = li.getAttribute("data-value");
      applyTheme(value);
      closeThemeDropdown();
    });
  });
  document.addEventListener("click", (e) => {
    if (
      !themeDropdownButton.contains(e.target) &&
      !themeDropdownMenu.contains(e.target)
    ) {
      closeThemeDropdown();
    }
  });
  function updateThemeDropdownUI(theme) {
    setThemeDropdownLabel(theme);
    themeDropdownMenu.querySelectorAll("li").forEach((li) => {
      li.setAttribute(
        "aria-selected",
        li.getAttribute("data-value") === theme ? "true" : "false"
      );
    });
  }
  // Helper to get current theme from <body> or localStorage
  function getCurrentTheme() {
    const bodyClass = document.body.className.match(/theme-([\w-]+)/);
    if (bodyClass && bodyClass[1]) return bodyClass[1];
    if (SELECTED_THEME_KEY && localStorage.getItem(SELECTED_THEME_KEY))
      return localStorage.getItem(SELECTED_THEME_KEY);
    return "default";
  }
  // On load, set label and highlight to actual current theme
  let theme = getCurrentTheme();
  setThemeDropdownLabel(theme);
  updateThemeDropdownUI(theme);
  // Patch applyTheme to update dropdown label and highlight
  return function patchedApplyTheme(theme) {
    applyTheme(theme);
    setThemeDropdownLabel(theme);
    updateThemeDropdownUI(theme);
  };
}
