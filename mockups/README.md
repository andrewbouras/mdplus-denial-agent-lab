# OrthoAppeals — patient-facing mockups

Clickable mockups of the same real service: a website where a patient whose
surgery was denied can build an insurance appeal. Every version is a working
**landing page / product front door** — a brand-new visitor arrives with
**nothing** and does everything themselves. Static HTML/CSS/vanilla-JS — **no
build step, no install, no network calls.** Built for a 69-year-old with low
tech comfort: large type, plain language, big buttons, fewest clicks.

## Open on your Mac

From this `mockups/` folder:

```bash
python3 -m http.server 8000 --bind 0.0.0.0
```

Then open **http://localhost:8000/** — you'll land on the **comparison hub**,
which links to every version below. (Each page also works from `file://` if you
just double-click its `.html`.)

## The versions

`index.html` is a **hub** that opens the two versions:

| Folder | Name | What's different |
|---|---|---|
| `map/` | **Version A · Guided** | One question at a time, with a roadmap side rail (done ✓ / current / grayed upcoming) so the full scope and progress are visible from screen one; persistent "always free, no email or card" line. On mobile the rail is a horizontal strip that keeps the active step in view. |
| `checklist-steps/` | **Version B · One page, step by step** | Everything on one scrollable, printable page, but each question stays grayed out until you answer the one above it, and the page glides the newly-opened step into view (Anish's idea) |

## Review notes baked in

The guided version (A) addresses two notes from the group: **always show how many
questions remain / progress to completion** (the roadmap side rail), and make it
clear the tool is **free with no sign-up or payment** (to avoid the "foot in the
door, then they ask for your credit card" feeling). Question copy across all
versions was warmed up toward a **friendly-helper** tone.

## Look & feel

Shared content lives in `assets/data.js`; shared styling in `assets/base.css`.
Display type is **Newsreader** (swapped in from Fraunces, whose "f" read as
wonky); body/UI type is **Public Sans**.

## Content is real, not lorem ipsum

The generic requirements a user is asked about (physical therapy, an
anti-inflammatory/NSAID trial, a knee injection, a knee X-ray report) and the
optional example case — Aetna, right total knee replacement, CPT 27447 — are
anchored on a real (synthetic-but-realistic) denial from
`../e2e/tests/denial-case.spec.js`. No specific medical thresholds (weeks of
care, BMI, arthritis grade) are invented.
