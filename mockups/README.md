# OrthoAppeals: patient-facing front end

The patient-facing website where someone whose surgery was denied can build an
insurance appeal. It is a working **landing page and product front door**: a
brand-new visitor arrives with **nothing** and does everything themselves.
Static HTML, CSS, and vanilla JavaScript, with **no build step, no install, and
no network calls.** Built for a 69-year-old with low tech comfort: large type,
plain language, big buttons, fewest clicks.

## Open on your Mac

From this `mockups/` folder:

```bash
python3 -m http.server 8000 --bind 0.0.0.0
```

Then open **http://localhost:8000/**. The root page sends you straight into the
app at `map/`. (The app also works from `file://` if you double-click
`map/index.html`.)

## The app

`map/index.html` is the front end. It asks one question at a time and keeps a
roadmap beside the question (done, current, upcoming) so the full scope and
progress are visible from the first screen.

The same page serves both devices. On a computer the roadmap is a sticky column
beside the question. On a phone it becomes a horizontal strip that keeps the
active step in view, and the denial-letter step asks for a camera photo instead
of a file attachment.

`checklist-steps/` is an earlier one-page layout kept for reference only. It is
no longer linked from the front door.

## Review notes baked in

The app addresses two notes from the group: **always show how many questions
remain and progress to completion** (the roadmap), and make it clear the tool is
**free with no sign-up or payment**, to avoid the "foot in the door, then they
ask for your credit card" feeling. Question copy was warmed up toward a
**friendly-helper** tone.

## Look & feel

Shared content lives in `assets/data.js`; shared styling in `assets/base.css`.
Display type is **Newsreader** (swapped in from Fraunces, whose "f" read as
wonky); body/UI type is **Public Sans**.

## Content is real, not lorem ipsum

The generic requirements a user is asked about (physical therapy, an
anti-inflammatory/NSAID trial, a knee injection, a knee X-ray report) and the
optional example case (Aetna, right total knee replacement, CPT 27447) are
anchored on a real (synthetic-but-realistic) denial from
`../e2e/tests/denial-case.spec.js`. No specific medical thresholds (weeks of
care, BMI, arthritis grade) are invented.
