## 2024-05-18 - Dashboard ARIA Compatibility
**Learning:** The auto-refreshing dashboard in `heidi_engine/dashboard.html` relies on continuous JavaScript polling to update DOM elements like `#status-badge`. Without `aria-live`, screen reader users miss critical status updates.
**Action:** Always add `aria-live="polite"` to dynamically updating text nodes in this dashboard to ensure accessibility without overwhelming the user with announcements.
