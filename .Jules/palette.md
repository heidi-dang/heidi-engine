## 2024-05-20 - Ensure Dynamic ARIA Progress Values Are Synced
**Learning:** For custom DOM-based progress bars (e.g., div-based elements instead of native `<progress>`), `aria-valuenow` must be explicitly managed by JavaScript synchronously alongside CSS width updates to ensure accurate reporting to screen readers.
**Action:** When creating custom progress indicators, ensure `aria-valuemin`, `aria-valuemax`, and a dynamically updated `aria-valuenow` are bound to the same lifecycle/update block as the visual representation.

## 2024-05-20 - Explicit Keyboard Focus for Custom Inputs
**Learning:** Accessibility standards require explicitly defining `:focus-visible` CSS rules for interactive elements (like custom links and selects) to ensure keyboard navigation outlines are visibly apparent when standard styling fails.
**Action:** Always provide robust `:focus-visible` rules for custom interactive components to ensure standard keyboard-navigable outlines.
