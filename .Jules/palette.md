## 2025-02-27 - Custom Progress Bar Accessibility
**Learning:** For custom DOM-based progress bars (e.g., div-based instead of native `<progress>`), `aria-valuenow` must be explicitly managed by JavaScript synchronously alongside CSS width updates to ensure accurate reporting to screen readers.
**Action:** Always verify that `aria-valuenow`, `aria-valuemin`, and `aria-valuemax` are present and updated on the parent container (using relative targeting like `element.parentElement`) to prevent brittle UI bindings in custom components.
