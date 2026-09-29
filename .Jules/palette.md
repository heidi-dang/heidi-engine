## 2026-09-29 - Progress Bar and Focus Ring Accessibility
**Learning:** Custom DOM-based progress bars (using divs) must have their `aria-valuenow` attribute explicitly synced via JavaScript alongside any CSS width updates to report correctly to screen readers. Also, custom styled interactive elements (like `select`) require explicit `:focus-visible` rules for keyboard navigation.
**Action:** Always verify custom component implementations against WAI-ARIA standards and sync ARIA attributes synchronously with state changes.
