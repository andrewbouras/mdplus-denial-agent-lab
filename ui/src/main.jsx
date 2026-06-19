import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  BookOpen,
  Check,
  ChevronRight,
  CircleAlert,
  FileSearch,
  Globe2,
  LoaderCircle,
  LockKeyhole,
  Play,
  Send,
  ShieldCheck,
  Upload,
  X,
} from "lucide-react";
import "./styles.css";

const apiPrefix = window.location.pathname.startsWith("/mdplus") ? "/mdplus" : "";
const apiUrl = (path) => `${apiPrefix}${path}`;

const emptyForm = {
  denial_letter: "",
  payer: "",
  plan_name: "",
  state: "",
  product_clue: "PPO",
  procedure: "",
  cpt: "",
  treating_practice: "",
  patient_notes: "",
  retrieval_mode: "both",
};

function Field({ label, children, hint }) {
  return (
    <label className="field">
      <span className="field-label">{label}</span>
      {children}
      {hint && <span className="field-hint">{hint}</span>}
    </label>
  );
}

function StatusMark({ status }) {
  if (status === "running") return <LoaderCircle className="spin" size={16} />;
  if (status === "completed") return <Check size={16} />;
  if (status === "failed") return <CircleAlert size={16} />;
  return <span className="status-dot" />;
}

function Timeline({ events = [] }) {
  const visible = events.slice(-9).reverse();
  return (
    <section className="timeline-panel">
      <div className="section-heading">
        <div>
          <h2>Live retrieval trace</h2>
          <p>Searches, document checks, and decisions stream here. No private reasoning is stored.</p>
        </div>
      </div>
      <div className="timeline">
        {visible.length === 0 ? (
          <div className="empty-state">Start a case to create the audit trail.</div>
        ) : (
          visible.map((event) => (
            <div className="timeline-row" key={event.event_id}>
              <div className={`timeline-node ${event.status || ""}`}>
                <StatusMark status={event.status} />
              </div>
              <div className="timeline-copy">
                <div className="timeline-meta">
                  <span>{event.arm?.replace("_", " ")}</span>
                  <time>{event.timestamp?.slice(11, 19)}</time>
                </div>
                <strong>{event.summary}</strong>
              </div>
            </div>
          ))
        )}
      </div>
    </section>
  );
}

function EvidencePanel({ episode, selectedArm, setSelectedArm, onReview, onRetry }) {
  const arms = episode?.arms || {};
  const arm = arms[selectedArm] || {};
  const result = arm.result;
  const retrieval = result?.retrieval || {};
  const policy = retrieval.selected_source;
  const review = episode?.source_reviews?.[selectedArm];
  const supportingOnly =
    policy?.evidence_role === "supporting_document" ||
    (selectedArm === "library_only" &&
      !policy?.evidence_role &&
      /form|checklist|code list|routing|precertification/i.test(
        `${policy?.source_type || ""} ${policy?.title || ""}`,
      ));
  const [notes, setNotes] = useState("");
  const [reviewBusy, setReviewBusy] = useState(false);
  const fileInput = React.useRef(null);

  async function submitReview(decision, file) {
    setReviewBusy(true);
    try {
      let upload;
      if (file) {
        const base64 = await new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => resolve(String(reader.result).split(",")[1]);
          reader.onerror = reject;
          reader.readAsDataURL(file);
        });
        upload = { name: file.name, media_type: file.type || "application/pdf", base64 };
      }
      await onReview({ arm: selectedArm, decision, notes, upload });
    } finally {
      setReviewBusy(false);
    }
  }
  return (
    <section className="evidence-panel">
      <div className="section-heading">
        <div>
          <h2>Source evidence</h2>
          <p>Selection, applicability, citations, and rejected alternatives.</p>
        </div>
      </div>
      <div className="tabs" role="tablist">
        <button
          className={selectedArm === "library_only" ? "active" : ""}
          onClick={() => setSelectedArm("library_only")}
        >
          <BookOpen size={15} /> Internal library
          <span className={`run-state ${arms.library_only?.runtime?.status || ""}`} />
        </button>
        <button
          className={selectedArm === "web_only" ? "active" : ""}
          onClick={() => setSelectedArm("web_only")}
        >
          <Globe2 size={15} /> Live web
          <span className={`run-state ${arms.web_only?.runtime?.status || ""}`} />
        </button>
      </div>
      {!result ? (
        <div className="evidence-loading">
          {arm.runtime?.status === "running" ? (
            <>
              <LoaderCircle className="spin" size={21} />
              <strong>Agent is retrieving policy evidence</strong>
              <span>Candidate sources and citations will appear here.</span>
            </>
          ) : (
            <>
              {arm.runtime?.status === "failed" ? <CircleAlert size={22} /> : <FileSearch size={22} />}
              <strong>{arm.runtime?.status === "failed" ? "Agent run failed" : "No result yet"}</strong>
              <span>
                {arm.runtime?.error || "This track has not produced a reviewable result."}
              </span>
              {arm.runtime?.status === "failed" && (
                <button className="retry-button" onClick={() => onRetry(selectedArm)}>
                  Retry this track
                </button>
              )}
            </>
          )}
        </div>
      ) : (
        <div className="evidence-content">
          <div className="result-status">
            <span>{result.status?.replaceAll("_", " ")}</span>
            <strong>{result.confidence?.overall || result.confidence || "Unrated"}</strong>
          </div>
          <div className="policy-block">
            <span className="overline">
              {supportingOnly ? "Supporting document — governing policy not retrieved" : "Selected governing policy"}
            </span>
            <h3>{policy?.title || "No policy selected"}</h3>
            <p>{policy?.url || policy?.path || "The agent recorded a blocker."}</p>
          </div>
          {policy && (
            <div className="document-frame">
              <iframe
                title="Selected insurance policy"
                src={apiUrl(`/api/episodes/${episode.manifest.episode_id}/source-document/${selectedArm}`)}
              />
              <div className="document-fallback">
                <FileSearch size={18} />
                <span>If the publisher blocks inline rendering, open the official source.</span>
                {policy.url && <a href={policy.url} target="_blank" rel="noreferrer">Open source</a>}
              </div>
            </div>
          )}
          <div className="applicability">
            {["payer", "product", "state", "procedure", "current"].map((item) => (
              <div key={item}>
                <Check size={14} />
                <span>{item}</span>
              </div>
            ))}
          </div>
          <div className="citation-list">
            <span className="overline">Cited support</span>
            {(retrieval.citations || []).slice(0, 4).map((citation, index) => (
              <div className="citation" key={index}>
                <span>{String(index + 1).padStart(2, "0")}</span>
                <p>{citation.excerpt || citation.claim || JSON.stringify(citation)}</p>
              </div>
            ))}
          </div>
          <div className="source-review">
            <span className="overline">
              {supportingOnly
                ? "This is not the governing policy"
                : "Is this the right governing policy for this patient?"}
            </span>
            {review ? (
              <div className={`review-record ${review.decision}`}>
                <ShieldCheck size={16} />
                <div>
                  <strong>{review.decision}</strong>
                  <span>
                    {review.library_promotion?.status === "promoted"
                      ? "Confirmed and saved to the internal library with provenance."
                      : "This accuracy label is recorded in the episode audit trail."}
                  </span>
                </div>
                {["rejected", "replaced"].includes(review.decision) &&
                  arm.runtime?.status === "failed" && (
                    <button className="inline-retry" onClick={() => onRetry(selectedArm)}>
                      Retry correction
                    </button>
                  )}
              </div>
            ) : (
              <>
                <textarea
                  rows="2"
                  value={notes}
                  onChange={(event) => setNotes(event.target.value)}
                  placeholder="Optional note about product, state, procedure, date, or vendor applicability…"
                />
                <div className="review-actions">
                  <button
                    disabled={reviewBusy || supportingOnly}
                    className="confirm"
                    title={supportingOnly ? "A supporting document cannot be confirmed as the governing policy." : ""}
                    onClick={() => submitReview("confirmed")}
                  >
                    <Check size={14} /> Confirm
                  </button>
                  <button disabled={reviewBusy} className="reject" onClick={() => submitReview("rejected")}>
                    <X size={14} /> Not correct
                  </button>
                  <button disabled={reviewBusy} onClick={() => fileInput.current?.click()}>
                    <Upload size={14} /> Upload mine
                  </button>
                  <button disabled={reviewBusy} onClick={() => submitReview("skipped")}>
                    Continue without feedback
                  </button>
                  <input
                    ref={fileInput}
                    className="hidden-input"
                    type="file"
                    accept=".pdf,.html,.htm,.txt,application/pdf,text/html,text/plain"
                    onChange={(event) => event.target.files?.[0] && submitReview("replaced", event.target.files[0])}
                  />
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </section>
  );
}

function NextAction({ episode, selectedArm }) {
  const result = episode?.arms?.[selectedArm]?.result;
  const steps = result?.next_steps;
  const interaction = result?.patient_interaction;
  if (!result) return null;
  const review = episode?.source_reviews?.[selectedArm];
  if (!review) {
    return (
      <section className="action-panel locked-action">
        <div className="action-icon"><LockKeyhole size={18} /></div>
        <div>
          <span className="overline">Next actionable step</span>
          <h2>Review the selected policy before continuing</h2>
          <p>Confirm, reject, upload a replacement, or continue without feedback.</p>
        </div>
      </section>
    );
  }
  if (review.decision === "rejected" || review.decision === "replaced") {
    return (
      <section className="action-panel locked-action">
        <div className="action-icon"><FileSearch size={18} /></div>
        <div>
          <span className="overline">Next actionable step</span>
          <h2>{review.decision === "replaced" ? "Replacement policy captured" : "Selected policy rejected"}</h2>
          <p>The downstream reasoning must be rerun against a corrected source before it is shown.</p>
        </div>
      </section>
    );
  }
  if (result.status === "needs_patient_follow_up") return null;
  return (
    <section className="action-panel">
      <div className="action-icon"><ChevronRight size={20} /></div>
      <div>
        <span className="overline">Next actionable step</span>
        <h2>{steps?.primary_action || "Further information is required"}</h2>
        <p>{steps?.safety_caveat || "This result remains an internal synthetic-case finding."}</p>
      </div>
      <div className="action-facts">
        <div>
          <span>Responsible party</span>
          <strong>{steps?.responsible_party || "Not established"}</strong>
        </div>
        <div>
          <span>Provider records</span>
          <strong>{interaction?.provider_records_needed?.length || 0} requested</strong>
        </div>
        <div>
          <span>Deadline</span>
          <strong>{steps?.deadline?.value || "Verify from letter"}</strong>
        </div>
      </div>
    </section>
  );
}

function PatientFollowUp({ episode, selectedArm, onSubmit }) {
  const result = episode?.arms?.[selectedArm]?.result;
  const review = episode?.source_reviews?.[selectedArm];
  const questions = result?.patient_interaction?.questions || [];
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  if (
    result?.status !== "needs_patient_follow_up" ||
    !questions.length ||
    !review ||
    ["rejected", "replaced"].includes(review.decision)
  ) return null;
  const question = questions[0];
  async function submit(event) {
    event.preventDefault();
    if (!answer.trim()) return;
    setBusy(true);
    try {
      await onSubmit({
        arm: selectedArm,
        question: question.text,
        answer: answer.trim(),
      });
      setAnswer("");
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="follow-up-panel">
      <div className="follow-up-copy">
        <span className="overline">Patient follow-up</span>
        <h2>{question.text}</h2>
        <p>{question.rationale}</p>
      </div>
      <form onSubmit={submit}>
        <textarea
          rows="3"
          value={answer}
          onChange={(event) => setAnswer(event.target.value)}
          placeholder="Paste the synthetic patient's answer exactly as provided…"
        />
        <button disabled={busy || !answer.trim()}>
          {busy ? <LoaderCircle className="spin" size={15} /> : <Send size={15} />}
          Submit answer
        </button>
      </form>
    </section>
  );
}

function EvaluationPanel({ episode, onEvaluate, onAdjudicate }) {
  const evaluation = episode?.evaluation;
  if (!episode || !evaluation) return null;
  const verdict = evaluation.verdict;
  const adjudication = evaluation.human_adjudication;
  const eligibility = evaluation.eligibility;
  if (!eligibility?.eligible && !verdict) {
    return (
      <section className="evaluation-panel muted-evaluation">
        <div>
          <span className="overline">Autonomous benchmark evaluation</span>
          <h2>Not ready for blinded scoring</h2>
          <p>{eligibility?.reasons?.[0] || "Complete the episode first."}</p>
        </div>
      </section>
    );
  }
  if (!verdict) {
    return (
      <section className="evaluation-panel">
        <div>
          <span className="overline">Autonomous benchmark evaluation</span>
          <h2>Frozen outputs are ready to compare with sealed truth</h2>
          <p>The answer key remains unavailable to retrieval and reasoning agents.</p>
        </div>
        <button
          onClick={onEvaluate}
          disabled={evaluation.runtime?.status === "running"}
        >
          {evaluation.runtime?.status === "running" ? (
            <LoaderCircle className="spin" size={15} />
          ) : (
            <ShieldCheck size={15} />
          )}
          {evaluation.runtime?.status === "running" ? "Evaluating" : "Run blinded evaluation"}
        </button>
      </section>
    );
  }
  return (
    <section className="evaluation-panel verdict-panel">
      <div>
        <span className="overline">Autonomous benchmark evaluation</span>
        <h2>{verdict.summary}</h2>
        <p>Human review priority: {verdict.human_review_priority}</p>
      </div>
      <div className="verdict-scores">
        {Object.entries(verdict.arms || {}).map(([arm, data]) => (
          <div key={arm}>
            <span>{arm.replace("_", " ")}</span>
            <strong>{data.overall?.score ?? "—"} / 4</strong>
          </div>
        ))}
      </div>
      {adjudication ? (
        <div className={`adjudication-record ${adjudication.decision}`}>
          <ShieldCheck size={15} />
          <span>Human: {adjudication.decision.replaceAll("_", " ")}</span>
        </div>
      ) : (
        <div className="adjudication-actions">
          <button onClick={() => onAdjudicate("confirmed")}>Confirm verdict</button>
          <button onClick={() => onAdjudicate("corrected")}>Disagree / correct</button>
          <button onClick={() => onAdjudicate("expert_review_required")}>Needs expert</button>
        </div>
      )}
    </section>
  );
}

function App() {
  const [form, setForm] = useState(emptyForm);
  const [episode, setEpisode] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [selectedArm, setSelectedArm] = useState("web_only");
  const [metrics, setMetrics] = useState(null);
  const [showMetrics, setShowMetrics] = useState(false);

  const episodeId = episode?.manifest?.episode_id;
  useEffect(() => {
    const fromUrl = new URLSearchParams(window.location.search).get("episode");
    if (!fromUrl) return;
    fetch(apiUrl(`/api/episodes/${fromUrl}`))
      .then((response) => response.json())
      .then((data) => {
        if (!data.error) {
          setEpisode(data);
          if (data.patient_submission) {
            setForm((current) => ({
              ...current,
              ...data.patient_submission,
            }));
          }
          if (data.arms?.library_only?.result) setSelectedArm("library_only");
        }
      });
  }, []);

  useEffect(() => {
    if (!episodeId) return;
    const timer = setInterval(async () => {
      const response = await fetch(apiUrl(`/api/episodes/${episodeId}`));
      if (response.ok) setEpisode(await response.json());
    }, 2500);
    return () => clearInterval(timer);
  }, [episodeId]);

  const running = useMemo(
    () =>
      Object.values(episode?.arms || {}).some(
        (arm) => arm.runtime?.status === "running",
      ),
    [episode],
  );

  function update(key, value) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function startEpisode(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const response = await fetch(apiUrl("/api/episodes"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Could not start episode");
      setEpisode(data);
      if (data.patient_submission) {
        setForm((current) => ({ ...current, ...data.patient_submission }));
      }
      window.history.replaceState(
        null,
        "",
        `${window.location.pathname}?episode=${data.manifest.episode_id}`,
      );
      setSelectedArm(form.retrieval_mode === "library_only" ? "library_only" : "web_only");
    } catch (caught) {
      setError(caught.message);
    } finally {
      setBusy(false);
    }
  }

  async function reviewSource(payload) {
    const response = await fetch(apiUrl(`/api/episodes/${episodeId}/source-feedback`), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Could not record source review");
    setEpisode(data);
  }

  async function submitFollowUp(payload) {
    const response = await fetch(apiUrl(`/api/episodes/${episodeId}/follow-up`), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Could not record follow-up");
    setEpisode(data);
  }

  async function retryArm(arm) {
    const response = await fetch(apiUrl(`/api/episodes/${episodeId}/retry-arm`), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ arm }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Could not retry agent");
    setEpisode(data);
  }

  async function runEvaluation() {
    const response = await fetch(apiUrl(`/api/episodes/${episodeId}/evaluate`), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Could not start evaluation");
    setEpisode(data);
  }

  async function adjudicate(decision) {
    const notes =
      decision === "confirmed"
        ? ""
        : window.prompt("Optional adjudication note:") || "";
    const response = await fetch(apiUrl(`/api/episodes/${episodeId}/adjudicate`), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decision, notes, corrections: {} }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Could not save adjudication");
    setEpisode(data);
  }

  async function toggleMetrics() {
    if (!showMetrics && !metrics) {
      const response = await fetch(apiUrl("/api/metrics"));
      setMetrics(await response.json());
    }
    setShowMetrics((value) => !value);
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark"><FileSearch size={18} /></div>
          <div>
            <h1>Denial Simulation Lab</h1>
            <p>Internal synthetic-patient evaluation</p>
          </div>
        </div>
        <div className="topbar-status">
          <button className="metrics-toggle" onClick={toggleMetrics}>
            Accuracy overview
          </button>
          <div><ShieldCheck size={16} /><span>Integrity verified</span></div>
          {episodeId && <code>{episodeId}</code>}
        </div>
      </header>

      <main>
        {showMetrics && metrics && (
          <section className="metrics-strip">
            <div>
              <span>Episodes</span>
              <strong>{metrics.episodes}</strong>
            </div>
            {["library_only", "web_only"].map((arm) => {
              const data = metrics.arms?.[arm] || {};
              const accuracy = data.confirmed_accuracy;
              return (
                <div key={arm}>
                  <span>{arm.replace("_", " ")} source accuracy</span>
                  <strong>
                    {accuracy == null ? "No labels" : `${Math.round(accuracy * 100)}%`}
                  </strong>
                  <small>{data.judged_source_selections || 0} judged selections</small>
                </div>
              );
            })}
            <div>
              <span>Sealed evaluations</span>
              <strong>{metrics.evaluated_episodes}</strong>
            </div>
          </section>
        )}
        <section className="workspace-grid">
          <form className="intake-panel" onSubmit={startEpisode}>
            <div className="section-heading intake-heading">
              <div>
                <h2>New synthetic case</h2>
                <p>Enter only what the simulated patient can provide.</p>
              </div>
              <LockKeyhole size={18} />
            </div>
            <Field label="Denial letter">
              <textarea
                rows="10"
                value={form.denial_letter}
                onChange={(e) => update("denial_letter", e.target.value)}
                placeholder="Paste the complete synthetic denial letter text…"
                required
              />
            </Field>
            <div className="field-grid">
              <Field label="Payer">
                <input value={form.payer} onChange={(e) => update("payer", e.target.value)} placeholder="e.g. Aetna" />
              </Field>
              <Field label="Plan name">
                <input value={form.plan_name} onChange={(e) => update("plan_name", e.target.value)} placeholder="As shown on card" />
              </Field>
              <Field label="State">
                <input value={form.state} onChange={(e) => update("state", e.target.value)} placeholder="FL" maxLength="20" />
              </Field>
              <Field label="Product clue">
                <select value={form.product_clue} onChange={(e) => update("product_clue", e.target.value)}>
                  <option>PPO</option><option>Commercial</option><option>Unknown</option><option>Other</option>
                </select>
              </Field>
              <Field label="Procedure or test">
                <input value={form.procedure} onChange={(e) => update("procedure", e.target.value)} placeholder="Patient's wording" />
              </Field>
              <Field label="CPT, if visible">
                <input value={form.cpt} onChange={(e) => update("cpt", e.target.value)} placeholder="Optional" />
              </Field>
            </div>
            <Field label="Patient notes" hint="Do not add facts the synthetic patient would not know.">
              <textarea
                rows="3"
                value={form.patient_notes}
                onChange={(e) => update("patient_notes", e.target.value)}
                placeholder="What the patient remembers, has tried, or is unsure about…"
              />
            </Field>
            <div className="run-options">
              {[
                ["both", "Run both"],
                ["library_only", "Library only"],
                ["web_only", "Web only"],
              ].map(([value, label]) => (
                <button
                  type="button"
                  key={value}
                  className={form.retrieval_mode === value ? "selected" : ""}
                  onClick={() => update("retrieval_mode", value)}
                >
                  {label}
                </button>
              ))}
            </div>
            {error && <div className="form-error">{error}</div>}
            <button className="primary-button" disabled={busy || running}>
              {busy ? <LoaderCircle className="spin" size={17} /> : <Play size={16} />}
              {running ? "Episode running" : "Start episode"}
            </button>
          </form>

          <Timeline events={episode?.events} />
          <EvidencePanel
            episode={episode}
            selectedArm={selectedArm}
            setSelectedArm={setSelectedArm}
            onReview={reviewSource}
            onRetry={retryArm}
          />
        </section>
        <PatientFollowUp
          episode={episode}
          selectedArm={selectedArm}
          onSubmit={submitFollowUp}
        />
        <NextAction episode={episode} selectedArm={selectedArm} />
        <EvaluationPanel
          episode={episode}
          onEvaluate={runEvaluation}
          onAdjudicate={adjudicate}
        />
      </main>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
