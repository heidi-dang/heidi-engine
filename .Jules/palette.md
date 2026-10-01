## 2024-02-12 - Dynamic ARIA bindings in Dashboard
**Learning:** For custom DOM-based progress bars (e.g., div-based elements instead of native `<progress>`), `aria-valuenow` must be explicitly managed by JavaScript synchronously alongside CSS width updates to ensure accurate reporting to screen readers.
**Action:** When creating custom HTML status indicators, ensure both static HTML ARIA roles and dynamic JavaScript ARIA attribute bindings are updated simultaneously.

## 2024-02-12 - Targeting dynamic elements
**Learning:** When dynamically updating parent container attributes in DOM via JavaScript, prefer relative targeting from specific child IDs (e.g., `document.getElementById('id').parentElement`) instead of generic class selectors to avoid brittle UI bindings.
**Action:** Use `.parentElement` or `.closest()` from a known ID to reliably update wrapper ARIA attributes when modifying inner element states.
