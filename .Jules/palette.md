## 2026-09-18 - DOM-based Progress Bar Accessibility
**Learning:** For custom DOM-based progress bars (div elements instead of native <progress>), 'aria-valuenow' must be explicitly managed by JavaScript synchronously alongside CSS width updates to ensure accurate reporting to screen readers. Also, explicit ':focus-visible' CSS rules should be defined for interactive elements (like links and selects).
**Action:** Always verify custom interactive components have matching ARIA attributes updated via JS and explicit focus states.
