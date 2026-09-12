## 2024-05-20 - [Focus Visible Styles]
**Learning:** This application lacks `:focus-visible` styling for interactive elements like inputs, selects, and links, which is crucial for keyboard navigation accessibility.
**Action:** Always add `:focus-visible` outlines to interactive elements.

## 2024-05-20 - [ARIA Progress Bars]
**Learning:** Custom UI components acting as progress bars lack appropriate ARIA roles and attributes for screen readers to interpret them correctly.
**Action:** For custom progress bars, add `role="progressbar"`, `aria-valuenow`, `aria-valuemin`, and `aria-valuemax` to communicate progress via accessibility APIs.
