
## 2024-09-13 - [Dashboard A11y]
**Learning:** Native `<select>` elements and `<div role="progressbar">` require explicit ARIA management (like `aria-label` and `aria-valuenow`) and `:focus-visible` styling when they aren't provided by a UI library in custom dashboards.
**Action:** Next time working on custom dashboards without external frameworks, ensure standard keyboard and screen-reader accessibility rules are applied (e.g., `aria-valuenow` dynamic updates and `focus-visible` outlines) to core components right away.
