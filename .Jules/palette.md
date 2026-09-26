## 2024-05-20 - Dynamic ARIA attributes in custom progress bars
**Learning:** For custom DOM-based progress bars (e.g., div-based elements instead of native `<progress>`), `aria-valuenow` must be explicitly managed by JavaScript synchronously alongside CSS width updates to ensure accurate reporting to screen readers. Static `role="progressbar"` is not enough.
**Action:** Always verify if a custom widget has an associated JavaScript lifecycle update function and attach the ARIA state update directly to it, rather than just adding static HTML attributes.
