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
        password: fd.get("password"),
        role: fd.get("role")
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
    localStorage.setItem("token", res.access_token);
    localStorage.setItem("role", fd.get("role") || role);
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

  return (
    <div style={{ fontFamily: "sans-serif", maxWidth: 900, margin: "2rem auto" }}>
      <h1>EAA Recruit Prototype</h1>
      {error && <p style={{ color: "crimson" }}>{error}</p>}

      {!token && (
        <>
          <h2>Register</h2>
          <form onSubmit={register}>
            <input name="email" placeholder="Email" required />
            <input name="full_name" placeholder="Full Name" required />
            <input name="password" placeholder="Password" type="password" required />
            <select
              name="role"
              onChange={(e) => {
                setRole(e.target.value);
                localStorage.setItem("role", e.target.value);
              }}
              value={role}
            >
              <option value="candidate">candidate</option>
              <option value="recruiter">recruiter</option>
              <option value="admin">admin</option>
            </select>
            <button type="submit">Register + Login</button>
          </form>
          <h2>Login</h2>
          <form onSubmit={login}>
            <input name="email" placeholder="Email" required />
            <input name="password" placeholder="Password" type="password" required />
            <input type="hidden" name="role" value={role} />
            <button type="submit">Login</button>
          </form>
        </>
      )}

      {token && (
        <>
          <button
            onClick={() => {
              setToken("");
              localStorage.removeItem("token");
            }}
          >
            Logout
          </button>
          <p>Role: {role}</p>

          {(role === "recruiter" || role === "admin") && (
            <>
              <h2>Create Job</h2>
              <form onSubmit={createJob}>
                <input name="title" placeholder="Title" required />
                <input name="description" placeholder="Description" required />
                <input name="required_skills" placeholder="Required skills csv" />
                <input name="cv_weight" placeholder="CV weight" defaultValue="0.6" />
                <input name="exam_weight" placeholder="Exam weight" defaultValue="0.4" />
                <input name="deadline" placeholder="YYYY-MM-DD" required />
                <button type="submit">Create</button>
              </form>
            </>
          )}

          <h2>Jobs</h2>
          {jobs.map((job) => (
            <div key={job.id} style={{ border: "1px solid #ddd", padding: "0.75rem", marginBottom: "0.5rem" }}>
              <strong>{job.title}</strong> ({job.status})<br />
              <small>{job.description}</small>
              <div style={{ marginTop: 8 }}>
                {(role === "recruiter" || role === "admin") && job.status !== "PUBLISHED" && (
                  <button onClick={() => publishJob(job.id)}>Publish</button>
                )}
                {(role === "recruiter" || role === "admin") && (
                  <button onClick={() => exportShortlist(job.id)}>Export CSV</button>
                )}
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
            </div>
          ))}

          <h2>Applications</h2>
          {apps.map((app) => (
            <div key={app.id} style={{ borderBottom: "1px solid #ddd", padding: "0.5rem 0" }}>
              App #{app.id} job:{app.job_id} status:{app.status} cv:{app.cv_score.toFixed(1)} exam:
              {app.exam_score.toFixed(1)} final:{app.final_score.toFixed(1)}
              <div>
                {(role === "candidate" || role === "admin") && (
                  <button onClick={() => submitExam(app.id)}>Submit Demo Exam</button>
                )}
                <button onClick={() => viewReport(app.id)}>View Report</button>
              </div>
            </div>
          ))}

          {report && (
            <>
              <h2>Explainable Report</h2>
              <p>{report.explanation_text}</p>
              <p>Top skills: {report.top_skills}</p>
            </>
          )}
        </>
      )}
    </div>
  );
}
