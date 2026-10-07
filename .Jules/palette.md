
## 2024-05-18 - Improve accessibility for progress bars and interactive elements
**Learning:** Adding `:focus-visible` to interactive elements (like custom `<select>` menus and links) ensures keyboard navigation remains highly visible without disrupting the standard mouse flow. Custom progress bars made with `div` elements require explicitly setting `role="progressbar"`, `aria-valuemin`, and `aria-valuemax`, and their JavaScript logic must synchronously manage `aria-valuenow` updates to be accessible.
**Action:** When updating width attributes dynamically via JavaScript in custom UI components, always ensure that relevant ARIA attributes (like `aria-valuenow`) are also explicitly updated simultaneously for screen readers.
