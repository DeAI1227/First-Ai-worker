# New Frontend Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a brand-new Supabase-first AI investment research terminal frontend from scratch with a dark, modern, high-density research-dashboard aesthetic.

**Architecture:** Create a standalone React + Vite + TypeScript frontend app that reads only Supabase production views and read-status tables. Keep the app shell, data layer, domain types, and page-specific components separated so the frontend can scale without reintroducing Python/output-JSON dependencies.

**Tech Stack:** React, Vite, TypeScript, Tailwind CSS, Supabase JS, lucide-react, lightweight chart-free UI, local mock-friendly empty/loading/error states.

---

### Task 1: Scaffold the standalone frontend app

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/index.html`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tailwind.config.ts`
- Create: `frontend/postcss.config.cjs`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/styles.css`
- Create: `frontend/src/env.d.ts`

- [ ] **Step 1: Write the app skeleton**

Create a Vite React app structure under `frontend/` with a clean app shell and route-ready layout.

- [ ] **Step 2: Verify the app builds**

Run: `cd frontend && npm run build`
Expected: build succeeds after dependencies are installed.

---

### Task 2: Add Supabase client, types, and query layer

**Files:**
- Create: `frontend/src/lib/supabase.ts`
- Create: `frontend/src/lib/types.ts`
- Create: `frontend/src/lib/queries.ts`
- Create: `frontend/src/lib/readStatus.ts`

- [ ] **Step 1: Define the page-facing types**

Mirror the Supabase view row contracts for dashboard, industries, stocks, stock detail events, macro, institution watch, reports, unread counts, and read status.

- [ ] **Step 2: Implement the query helpers**

Add typed helpers for:
`getDashboardEvents`, `getIndustryCards`, `getStockCards`, `getStockDetailEvents`, `getMacroEvents`, `getInstitutionWatchEvents`, `getRecentReports`, `getUnreadCounts`.

- [ ] **Step 3: Implement read-status helpers**

Add `markEventRead` and `markReportRead`, writing only to `user_read_status`.

- [ ] **Step 4: Verify Supabase env handling**

Run: `cd frontend && npm run build`
Expected: build succeeds when env vars are present; runtime throws a clear error if missing.

---

### Task 3: Build the app shell and navigation

**Files:**
- Create: `frontend/src/components/layout/AppShell.tsx`
- Create: `frontend/src/components/layout/Sidebar.tsx`
- Create: `frontend/src/components/layout/Topbar.tsx`
- Create: `frontend/src/components/layout/PageFrame.tsx`

- [ ] **Step 1: Build the shell**

Implement a dark, premium research-terminal shell with sidebar, top bar, and responsive content framing.

- [ ] **Step 2: Wire route navigation**

Use route-aware links for Dashboard, Industries, Stocks, Macro, Institution Watch, Reports, and Settings/System.

- [ ] **Step 3: Verify responsive behavior**

Run the app and confirm the shell collapses cleanly on smaller widths.

---

### Task 4: Build shared UI primitives and state components

**Files:**
- Create: `frontend/src/components/ui/Button.tsx`
- Create: `frontend/src/components/ui/Card.tsx`
- Create: `frontend/src/components/ui/Badge.tsx`
- Create: `frontend/src/components/ui/EmptyState.tsx`
- Create: `frontend/src/components/ui/LoadingState.tsx`
- Create: `frontend/src/components/ui/ErrorState.tsx`
- Create: `frontend/src/components/ui/StatPill.tsx`
- Create: `frontend/src/components/ui/QualitySummaryMini.tsx`

- [ ] **Step 1: Build consistent primitives**

Create reusable primitives for cards, badges, CTA buttons, and page states using the same visual system.

- [ ] **Step 2: Make quality summary readable**

Create a compact stats block for `quality_summary` with clear counts and color coding.

- [ ] **Step 3: Verify states render cleanly**

Run the app with empty/mock state data and verify loading/error/empty states are visually coherent.

---

### Task 5: Implement the main pages

**Files:**
- Create: `frontend/src/pages/DashboardPage.tsx`
- Create: `frontend/src/pages/IndustriesPage.tsx`
- Create: `frontend/src/pages/StocksPage.tsx`
- Create: `frontend/src/pages/StockDetailPage.tsx`
- Create: `frontend/src/pages/MacroPage.tsx`
- Create: `frontend/src/pages/InstitutionWatchPage.tsx`
- Create: `frontend/src/pages/ReportsPage.tsx`
- Create: `frontend/src/pages/SettingsPage.tsx`

- [ ] **Step 1: Dashboard**

Show today’s important events, critical/important/general counts, recent events, unread summary, and a quality summary module.

- [ ] **Step 2: Industries**

Render six industry cards with counts and latest update time.

- [ ] **Step 3: Stocks**

Render all 45 tracked stocks from reference data with industry tags, event count, and latest event time.

- [ ] **Step 4: Stock detail**

Show an event stream for the selected stock; if no rows are returned, render an empty state instead of fake events.

- [ ] **Step 5: Macro, institution watch, reports, settings**

Implement the remaining sections with the same data and state conventions.

- [ ] **Step 6: Verify no fake no-news events**

Check that the UI never invents a “today no major update” event.

---

### Task 6: Add routing and page-level data loading

**Files:**
- Create: `frontend/src/router.tsx`
- Modify: `frontend/src/App.tsx`
- Create: `frontend/src/hooks/useQuery.ts`
- Create: `frontend/src/hooks/useUnreadCounts.ts`

- [ ] **Step 1: Wire page routes**

Set up routes for the eight frontend pages.

- [ ] **Step 2: Add async loading flow**

Use loading, error, and empty states per page while fetching Supabase data.

- [ ] **Step 3: Verify route transitions**

Navigate between pages and confirm data updates without layout shift.

---

### Task 7: Add README and docs for the new frontend

**Files:**
- Create: `frontend/README.md`

- [ ] **Step 1: Document setup**

Explain environment variables, install steps, and run commands.

- [ ] **Step 2: Document data rules**

State clearly that the frontend reads Supabase production views only and never reads Python or output JSON.

- [ ] **Step 3: Document page-to-view mapping**

List the Supabase view for each page.

---

### Task 8: Verify and polish

**Files:**
- Modify: `frontend/src/**` as needed
- Modify: `tests/**` as needed for file-existence or contract checks

- [ ] **Step 1: Run tests**

Run `python -m unittest discover -s tests -p "test_*.py" -v` and `python -m compileall .`.

- [ ] **Step 2: Build the frontend**

Run `cd frontend && npm run build`.

- [ ] **Step 3: Fix visual drift**

If the rendered app looks too generic, tighten typography, spacing, density, and contrast until it reads like a premium research terminal.

- [ ] **Step 4: Commit**

Commit the new frontend scaffold and docs together once the app is working.

