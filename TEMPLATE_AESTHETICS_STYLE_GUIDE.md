# Oreno GRC Template Aesthetics & Sectioning Guide

Purpose: Provide a reusable, non-functional style standard for web templates across apps (Risk, Audit, Compliance, Legal, Contracts, AI Governance, etc.). Implements the same card/sectioning look-and-feel seen in COBIT capability/process templates.

## 1. Page Anatomy (Default)
- Top bar: title + context metadata + compact action buttons (right-aligned)
- Content grid: two columns on lg+ screens, single column on md- screens
  - Main column (lg: 8/12): primary content cards (information, description, details)
  - Sidebar (lg: 4/12): quick actions, related items, KPIs/mini-summaries

## 2. Section Cards
- Each section MUST be rendered as a Bootstrap card
- Card structure:
  - `<div class="card">`
    - `<div class="card-header"><strong>Section Title</strong></div>`
    - `<div class="card-body"> ... content ... </div>`
- Use multiple compact cards instead of a single long card
- Spacing: apply `mt-3` between vertically stacked cards

## 3. Titles, Metadata, Actions
- Page title: `h2.mb-1`
- Metadata line under title for key identifiers (codes, owners, dates)
- Actions: right-aligned button group with compact buttons
  - Use `btn btn-outline-secondary btn-sm` for neutral actions
  - Use `btn btn-outline-danger btn-sm` for destructive
  - Use icons (Bootstrap Icons) where meaningful (e.g., `bi-pencil`, `bi-trash`, `bi-arrow-left`)

## 4. Tables & Field Blocks
- Prefer small, clean tables for label/value pairs:
  - `table table-sm` with 2 or 4 columns (label/value pairs)
  - Left column width: `w-25` or explicit `style="width:20%"` for labels
- For narrative content:
  - Wrap in `<div class="content-wrapper">` to keep consistent spacing
- For grouped blocks inside cards:
  - Optional utility pattern:
    - `<div class="field-group">`
      - `<div class="field-label">Label</div>`
      - `<div class="field-value">Value/content</div>`
    - Only if needed for readability; otherwise, use simple tables or paragraphs

## 5. Sidebar Patterns
- Quick Actions card
  - Title: `Quick Actions`
  - Body uses a vertical button stack: `d-grid gap-2`
  - Buttons: `btn btn-outline-primary btn-sm`
- Related Items card
  - Title: `Related Items`
  - Body uses rows with label + count badge
  - Count badge: `badge bg-secondary`

## 6. Badges & Status Chips
- Use Bootstrap badges for compact indicators
  - Neutral meta (codes): `badge bg-primary` or `bg-secondary`
  - Status pills:
    - Approved/low risk → `status-badge status-approved` or `risk-level risk-low`
    - Pending/medium risk → `status-badge status-pending` or `risk-level risk-medium`
    - Rejected/high risk → `status-badge status-rejected` or `risk-level risk-high`
- These classes are already defined in `reports/base_report.html` for reports and can be paralleled in web if needed; keep visual consistency

## 7. Content Order by Object Type
- Processes / Domains (COBIT, NIST structures)
  1) Information (code, name, dates)
  2) Description / Purpose
  3) Objectives / Goals / Outcomes
  4) Practices / Controls / Links
  5) Sidebar: Quick Actions, Related Items
- Risks / Issues / Incidents
  1) Key metadata (codes, status, owner)
  2) Assessment metrics (impact/likelihood/score or severity/priority)
  3) Narrative (description, root cause, actions)
  4) Evidence / Attachments / Relationships
  5) Sidebar: Quick Actions, Related Items
- Reports (HTML pages)
  - Keep the same card visual hierarchy, but prefer summary tables over large stat tiles

## 8. Lists vs. Tables
- Prefer compact tables for metrics and key-value data
- Use bullet lists for concise, ordered steps or goals
- Avoid large stat tiles that waste vertical space; prefer a single-row table with 3–5 metrics

## 9. Icons & Text
- Use Bootstrap Icons for clarity, but don’t overuse
- Keep labels short; expand in tooltips if needed

## 10. Responsiveness
- Grid: `row g-3` and `col-lg-8 / col-lg-4`
- Ensure long content wraps; avoid horizontal scroll

## 11. DOs and DON’Ts
- DO
  - Use multiple, titled cards to break content logically
  - Keep actions compact and right-aligned
  - Use small tables for facts; lists for goals/practices
  - Keep whitespace balanced (not cramped, not wasteful)
- DON’T
  - Combine unrelated content in one card
  - Use large metric tiles where a table row suffices
  - Duplicate cover/meta content on page (avoid repetition)

## 12. Example Skeleton (Web Detail Page)
```html
<div class="d-flex justify-content-between align-items-center mb-3">
  <div>
    <h2 class="mb-1">Object Title</h2>
    <div class="text-muted">Code: <span class="badge bg-primary">ABC01</span></div>
  </div>
  <div class="btn-group">
    <a href="#" class="btn btn-outline-secondary btn-sm"><i class="bi bi-pencil"></i> Edit</a>
    <a href="#" class="btn btn-outline-danger btn-sm"><i class="bi bi-trash"></i> Delete</a>
    <a href="#" class="btn btn-outline-secondary btn-sm"><i class="bi bi-arrow-left"></i> Back</a>
  </div>
</div>

<div class="row g-3">
  <div class="col-lg-8">
    <div class="card">
      <div class="card-header"><strong>Information</strong></div>
      <div class="card-body">
        <table class="table table-sm mb-0">
          <tr><th class="w-25">Code</th><td>ABC01</td></tr>
          <tr><th>Name</th><td>Sample Name</td></tr>
        </table>
      </div>
    </div>

    <div class="card mt-3">
      <div class="card-header"><strong>Description</strong></div>
      <div class="card-body"><div class="content-wrapper">...</div></div>
    </div>
  </div>

  <div class="col-lg-4">
    <div class="card">
      <div class="card-header"><strong>Quick Actions</strong></div>
      <div class="card-body d-grid gap-2">
        <a href="#" class="btn btn-outline-primary btn-sm">Primary Action</a>
      </div>
    </div>

    <div class="card mt-3">
      <div class="card-header"><strong>Related Items</strong></div>
      <div class="card-body">
        <div class="d-flex justify-content-between mb-2"><div>Items</div><span class="badge bg-secondary">3</span></div>
      </div>
    </div>
  </div>
</div>
```

## 13. Implementation Notes
- Prefer enhancing existing templates with cards/sections without changing underlying logic
- Keep IDs, URLs, and context variables unchanged to avoid breaking behavior
- Align with the report templates’ professional tone (consistent typography, spacing, badges)

---
Version: 1.0  
Scope: Web templates across apps (non-report HTML)  
Status: Adopted in COBIT capability/process; use for all new/updated templates
