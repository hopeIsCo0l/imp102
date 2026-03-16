import { useEffect, useMemo, useState } from "react";
import { api } from "./api";

export default function App() {
  const [token, setToken] = useState(localStorage.getItem("token") || "");
  const [role, setRole] = useState(localStorage.getItem("role") || "candidate");
  const [jobs, setJobs] = useState([]);
  const [apps, setApps] = useState([]);
  const [error, setError] = useState("");
  const [report, setReport] = useState(null);

  const authHeaders = useMemo(() => ({ token }), [token]);

  async function register(e) {
    e.preventDefault();
    setError("");
    const fd = new FormData(e.currentTarget);
    await api("/auth/register", {
      method: "POST",
      body: {
        email: fd.get("email"),
        full_name: fd.get("full_name"),
        password: fd.get("password")
      }
    });
    await login(e);
  }

  async function login(e) {
    e.preventDefault();
    setError("");
    const fd = new FormData(e.currentTarget);
    const res = await api("/auth/login", {
      method: "POST",
      body: {
        email: fd.get("email"),
        password: fd.get("password")
      }
    });
    setToken(res.access_token);
    setRole(res.user.role);
    localStorage.setItem("token", res.access_token);
    localStorage.setItem("role", res.user.role);
  }

  async function loadCurrentUser() {
    if (!token) return;
    const user = await api("/auth/me", authHeaders);
    setRole(user.role);
    localStorage.setItem("role", user.role);
  }

  async function loadJobs() {
    if (!token) return;
    const rows = await api("/jobs", authHeaders);
    setJobs(rows);
  }

  async function loadApps() {
    if (!token) return;
    const rows = await api("/applications/mine", authHeaders);
    setApps(rows);
  }

  useEffect(() => {
    loadCurrentUser().catch((e) => setError(e.message));
    loadJobs().catch((e) => setError(e.message));
    loadApps().catch((e) => setError(e.message));
  }, [token]);

  async function createJob(e) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    await api("/jobs", {
      method: "POST",
      ...authHeaders,
      body: {
        title: fd.get("title"),
        description: fd.get("description"),
        required_skills: fd.get("required_skills"),
        cv_weight: Number(fd.get("cv_weight")),
        exam_weight: Number(fd.get("exam_weight")),
        deadline: fd.get("deadline"),
        status: "DRAFT"
      }
    });
    await loadJobs();
  }

  async function publishJob(jobId) {
    await api(`/jobs/${jobId}/publish`, { method: "POST", ...authHeaders });
    await loadJobs();
  }

  async function applyToJob(jobId, file) {
    const form = new FormData();
    form.append("file", file);
    await api(`/applications/${jobId}/submit`, {
      method: "POST",
      token,
      body: form,
      headers: {}
    });
    await loadApps();
  }

  async function submitExam(applicationId) {
    await api(`/exams/${applicationId}/submit`, {
      method: "POST",
      ...authHeaders,
      body: {
        answers:
          "Airline Transport Pilot License and safety preflight procedure are essential."
      }
    });
    await loadApps();
  }

  async function viewReport(applicationId) {
    const rep = await api(`/applications/${applicationId}/report`, authHeaders);
    setReport(rep);
  }

  async function exportShortlist(jobId) {
    const blob = await api(`/recruiter/jobs/${jobId}/export`, authHeaders);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `shortlist_job_${jobId}.csv`;
    a.click();
  }

  const isManager = role === "recruiter" || role === "admin";

  return (
    <div className="app-shell">
      <div className="app-bg-glow app-bg-glow-a" />
      <div className="app-bg-glow app-bg-glow-b" />
      <main className="container">
        <header className="hero">
          <p className="kicker">AI-assisted recruitment</p>
          <h1>EAA Recruit</h1>
          <p className="hero-subtitle">Screen candidates, run assessments, and export shortlists in one place.</p>
        </header>

        {error && <div className="error-banner">{error}</div>}

        {!token && (
          <section className="grid grid-auth">
            <article className="panel">
              <h2>Create account</h2>
              <p className="muted">Public signup creates a candidate account. Recruiter/admin accounts are admin-managed.</p>
              <form className="form-grid" onSubmit={register}>
                <input name="email" placeholder="Email" required />
                <input name="full_name" placeholder="Full Name" required />
                <input name="password" placeholder="Password" type="password" required />
                <button type="submit">Register + Login</button>
              </form>
            </article>

            <article className="panel">
              <h2>Sign in</h2>
              <form className="form-grid" onSubmit={login}>
                <input name="email" placeholder="Email" required />
                <input name="password" placeholder="Password" type="password" required />
                <button type="submit">Login</button>
              </form>
            </article>
          </section>
        )}

        {token && (
          <>
            <section className="topbar panel">
              <div>
                <p className="small-label">Signed in as</p>
                <p className="role-pill">{role}</p>
              </div>
              <button
                className="ghost-btn"
                onClick={() => {
                  setToken("");
                  localStorage.removeItem("token");
                }}
              >
                Logout
              </button>
            </section>

            {isManager && (
              <section className="panel">
                <h2>Create Job</h2>
                <form className="form-grid job-grid" onSubmit={createJob}>
                  <input name="title" placeholder="Title" required />
                  <input name="description" placeholder="Description" required />
                  <input name="required_skills" placeholder="Required skills csv" />
                  <input name="cv_weight" placeholder="CV weight" defaultValue="0.6" />
                  <input name="exam_weight" placeholder="Exam weight" defaultValue="0.4" />
                  <input name="deadline" placeholder="YYYY-MM-DD" required />
                  <button type="submit">Create</button>
                </form>
              </section>
            )}

            <section className="panel">
              <h2>Jobs</h2>
              <div className="card-list">
                {jobs.map((job) => (
                  <article key={job.id} className="card">
                    <div className="card-head">
                      <strong>{job.title}</strong>
                      <span className={`status status-${job.status.toLowerCase()}`}>{job.status}</span>
                    </div>
                    <p className="muted">{job.description}</p>
                    <div className="action-row">
                      {isManager && job.status !== "PUBLISHED" && (
                        <button onClick={() => publishJob(job.id)}>Publish</button>
                      )}
                      {isManager && <button onClick={() => exportShortlist(job.id)}>Export CSV</button>}
                      {role === "candidate" && job.status === "PUBLISHED" && (
                        <input
                          type="file"
                          onChange={(e) => {
                            const file = e.target.files?.[0];
                            if (file) applyToJob(job.id, file).catch((er) => setError(er.message));
                          }}
                        />
                      )}
                    </div>
                  </article>
                ))}
              </div>
            </section>

            <section className="panel">
              <h2>Applications</h2>
              <div className="card-list">
                {apps.map((app) => (
                  <article key={app.id} className="card">
                    <div className="card-head">
                      <strong>
                        App #{app.id} / Job #{app.job_id}
                      </strong>
                      <span className={`status status-${app.status.toLowerCase()}`}>{app.status}</span>
                    </div>
                    <p className="muted">
                      CV {app.cv_score.toFixed(1)} | Exam {app.exam_score.toFixed(1)} | Final{" "}
                      {app.final_score.toFixed(1)}
                    </p>
                    <div className="action-row">
                      {(role === "candidate" || role === "admin") && (
                        <button onClick={() => submitExam(app.id)}>Submit Demo Exam</button>
                      )}
                      <button onClick={() => viewReport(app.id)}>View Report</button>
                    </div>
                  </article>
                ))}
              </div>
            </section>

            {report && (
              <section className="panel report">
                <h2>Explainable Report</h2>
                <p>{report.explanation_text}</p>
                <p className="muted">Top skills: {report.top_skills}</p>
              </section>
            )}
          </>
        )}
      </main>
    </div>
  );
}
