## 2026-10-05 - Dynamic Progress Bar Accessibility
**Learning:** For custom DOM-based progress bars (e.g., div-based elements instead of native `<progress>`), `aria-valuenow` must be explicitly managed by JavaScript synchronously alongside CSS width updates to ensure accurate reporting to screen readers.
**Action:** When updating a custom progress bar visually, dynamically set its parent container's `aria-valuenow` attribute using relative DOM targeting (`parentElement.setAttribute`).

## 2026-10-05 - Explicit Focus States for Interactive Elements
**Learning:** Accessibility standards require explicitly defining `:focus-visible` CSS rules for interactive elements like links (`a`) and selects (`select`) to improve keyboard navigation without compromising mouse interaction aesthetics.
**Action:** Always add explicit `:focus-visible` styles with sufficient outline contrast (e.g., `outline: 2px solid var(--accent-color)`) for all navigable UI elements in dashboards.
