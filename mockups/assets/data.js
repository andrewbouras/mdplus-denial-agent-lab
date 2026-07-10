/* Shared mockup content.
 * DEFAULT STATE IS EMPTY / FROM ZERO — a brand-new visitor has provided nothing.
 * `requirements` is the GENERIC "what insurers usually ask for" list (no patient
 * specifics). `example` holds the optional Maria demo, whose wording is taken from
 * the real source e2e/tests/denial-case.spec.js. No invented medical numbers.
 * Nothing here makes a network call. */
window.APPEAL = {
  product: {
    name: "OrthoAppeals",
    tagline: "Your knee replacement was denied? You can fight it — for free.",
    promise:
      "Insurance denials are often just missing paperwork, not a final no. We walk you through it in plain language and help you build a strong appeal — step by step.",
    reassure: "Most denials like this can be appealed. Let's do it together.",
  },

  // Common starting choices for a brand-new user (they pick or type their own).
  surgeries: [
    "Knee replacement",
    "Hip replacement",
    "Shoulder surgery",
    "Another surgery",
  ],

  // GENERIC requirements insurers usually want before a knee replacement.
  // Shown to a user who arrives with nothing — not tied to any one person.
  requirements: [
    {
      id: "pt",
      q: "Did you ever go to physical therapy for your knee?",
      title: "Physical therapy records",
      plain: "The notes and attendance dates from your physical therapy visits.",
      why: "Insurers usually like to see you gave physical therapy a real try first — so this one really helps your case.",
      how: "Give your physical therapy clinic a call and ask them to send over your visit notes and dates.",
    },
    {
      id: "meds",
      q: "Did you take any anti-inflammatory medicine for the pain?",
      title: "Anti-inflammatory medicine (NSAID)",
      plain: "A note that you took an anti-inflammatory medicine to ease the pain.",
      why: "Medicine counts as one of the treatments insurers expect you to try first, so it's worth including.",
      how: "Your doctor's office can confirm this straight from your chart — no hunting required.",
    },
    {
      id: "injection",
      q: "Did you get any shots (injections) in your knee?",
      title: "Knee injection record",
      plain: "A note about any injection you had in the knee, and how it went.",
      why: "An injection is another treatment insurers like to see you tried — every bit adds to your case.",
      how: "Your doctor's office can add this from your chart for you.",
    },
    {
      id: "xray",
      q: "Have you had any X-rays of your knee?",
      title: "Knee X-ray report",
      plain: "The written report from your knee X-rays — not just the images.",
      why: "Insurers want the report that describes the wear in your knee joint, so this is a key piece.",
      how: "Call the imaging center and ask them to send the written report to your surgeon — they do this all the time.",
    },
  ],

  // OPTIONAL demo only — loaded when the user clicks "See an example".
  example: {
    name: "Maria Torres",
    plan: "Aetna Open Choice PPO",
    surgery: "Knee replacement",
    deniedOn: "June 9, 2026",
    cpt: "27447",
    denialLetter:
      "We are unable to approve the requested right total knee arthroplasty at this time. The clinical information submitted does not demonstrate that the member has completed and failed the required course of nonsurgical treatment. The submission also does not include sufficient radiographic documentation of qualifying advanced joint disease. The records did not include physical therapy attendance or progress records, dates and outcomes of other conservative treatment, or the formal knee radiology report.",
    // Her plain-language answers, keyed to the requirement ids (from the source).
    answers: {
      pt: "Yes — physical therapy at Harbor Rehabilitation, about September to mid-November 2025.",
      meds: "Yes — I took meloxicam for several months and stopped because it upset my stomach.",
      injection: "Yes — one knee injection around December 2025 that helped for about two weeks.",
      xray: "Yes — X-rays at Suncoast Imaging, but I don't have the written report at home.",
    },
  },
};
