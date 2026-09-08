## 2024-11-20 - [CSS Styling for Keyboard A11y without Utility Frameworks]
**Learning:** This app's static HTML files (`heidi_engine/dashboard.html`) do not utilize utility CSS frameworks (like Tailwind). Styling complex interactive pseudo-classes (like `:hover` and `:focus-visible`) cannot be achieved using `style=""` tags and requires defining a custom CSS class in the header block.
**Action:** When adding interaction feedback (hover borders, focus rings) to elements without utility classes, inject a minimal `<style>` rule rather than attempting inline styles.
