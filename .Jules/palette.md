## 2026-09-30 - DOM-based Progress Bar Accessibility
**Learning:** For custom DOM-based progress bars (e.g., div-based elements instead of native `<progress>`), `aria-valuenow` must be explicitly managed by JavaScript synchronously alongside CSS width updates to ensure accurate reporting to screen readers.
**Action:** Always ensure any dynamic visual indicators of progress have corresponding logic to update their ARIA attributes.
