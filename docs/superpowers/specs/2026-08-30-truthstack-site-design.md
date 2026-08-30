# Truthstack marketing site — design

Status: approved by user, 2026-08-30
Repo: new, separate from PULSE — `~/Workspace/truthstack-site`, GitHub repo to be created and pushed during implementation

## Purpose

Marketing/lead-gen website for Truthstack, a QA/software-testing consultancy. Site presents services, drives contact-form leads. No backend, no user accounts, no dynamic data beyond form submission.

## Company name

**Truthstack**. Checked for collisions (2026-08-30 web search): no software-testing/QA company uses this name. Unrelated small projects exist elsewhere (a whistleblower-fund site, a GitHub MCP tool, an unrelated monorepo) — none in the testing space, none appear to be registered trademarks. Considered and rejected: TestForge (multiple existing testing companies use it), TestStack (existing testing-tool OSS project + existing test-orchestration company), QualityStack (no exact collision, but too close to existing Qualitest/QualityLogic).

Domain registration is the user's own action — not covered by this build.

## Architecture

- Next.js 15 (App Router) + React + TypeScript + Tailwind CSS
- Fully static/client-rendered — no backend, no database, no API routes
- Hosting: Vercel via GitHub integration (auto preview deploy per PR, auto prod deploy on merge to `main`) — configured once repo is linked in Vercel dashboard, not scripted
- CI: GitHub Actions workflow on PR — install deps, ESLint, `tsc` typecheck, build. Gates merge; deploy itself is Vercel's job, not the Action's
- Framer Motion for animation (scroll-reveal, hover, hero background)

## Pages

- **Home** — animated hero (headline, CTA, subtle particle/gradient background), 8-service overview grid (icon + one-liner, links to Services), social-proof strip (logo/testimonial placeholders — real content added later by user), animated stat counters, bottom CTA to Contact
- **Services** — full detail for all 8 services: software testing, AI-capability testing, AI model testing, test consultants, testing solutions, test-strategy audits, CI/CD pipeline setup, testing-as-a-service. Each gets description, "what's included," CTA to Contact
- **About** — company story/mission copy, team section left as placeholder cards (no real people supplied yet)
- **Pricing** — engagement-model cards, not fixed dollar tiers (QA consulting is customarily custom-scoped): Project-based, Staff augmentation, Testing-as-a-Service retainer. Each: what's included + "Get a quote" CTA to Contact
- **Contact** — form: name, email, company, service-interest dropdown, message. Client-side submit to Formspree (or equivalent form-backend service) — no server code
- **404** — custom not-found page

## Visual style

Dark theme, techy: dark background, neon green/cyan accent, monospace touches for a dev-tool/QA feel. Interactive touches: hover-expand service cards, scroll-reveal animations, animated stat counters.

## Data flow

Fully static. The only external call is the contact form's client-side POST to the form-backend service (Formspree or equivalent). No database, no server, no API routes.

## Error handling

- Client-side form validation (required fields, email format) before submit
- Form-backend service's success/failure response shown inline on the Contact page
- Custom 404 page for unmatched routes
- TypeScript + ESLint catch errors at build time; CI blocks a broken build from reaching preview or prod

## Testing

Playwright smoke test in CI: all pages render, nav works, contact form submits successfully (against the form-backend's test/sandbox mode). Deliberately minimal — golden-path coverage only, not exhaustive; using Playwright here doubles as a nod to Truthstack's own product category.

## Open items (user-owned, outside this build)

- Domain name registration and DNS pointing to Vercel
- Formspree (or equivalent) account creation and form endpoint ID
- Vercel account + linking the GitHub repo (dashboard action, one-time)
- Real logo, team photos, testimonials/client logos — placeholders ship until supplied
- GitHub repo creation under user's account and initial push
