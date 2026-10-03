
## 2024-05-19 - Synchronized ARIA Attributes for Custom Progress Bars
**Learning:** Custom DOM-based progress bars (using `div`s rather than native `<progress>`) require explicit, synchronous updates to `aria-valuenow` via JavaScript alongside visual CSS width changes to ensure screen readers accurately announce progress.
**Action:** Always map the calculated percentage logic to update `aria-valuenow` on the parent element containing `role="progressbar"` when dynamically updating visual representations.

## 2024-05-19 - Keyboard Accessibility Focus Visibility
**Learning:** Default focus styles are often insufficient or missing in custom-styled dashboards, making keyboard navigation difficult for interactive elements like `<select>` or `<a>`.
**Action:** Ensure `:focus-visible` styles are explicitly defined for all interactive elements to provide a prominent outline, aiding keyboard-only users without compromising the default design for mouse users.
