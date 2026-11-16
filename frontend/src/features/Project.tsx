import PortfolioSettings from "./PortfolioSettings";
import {
  ArrowUpRight,
  Check,
  CheckCircle2,
  Clock,
  MapPin,
  MessagesSquare,
  Plus,
  Upload,
} from "lucide-react";
import { useEffect, useState } from "react";
import { api, date, Row, short, upload } from "../api";
import {
  Badge,
  Button,
  Empty,
  Field,
  Form,
  obj,
  Select,
  Text,
} from "../components/ui";
import ExecutionPanel from "./ExecutionPanel";
import Finance from "./Finance";

export default function ProjectDetail({
  project: p,
  user,
  people,
  notify,
  refreshParent,
  back,
}: {
  project: Row;
  user: Row;
  people: Row[];
  notify: (s: string) => void;
  refreshParent: () => void;
  back: () => void;
}) {
  const [tab, setTab] = useState("Milestones");
  const [milestones, setMilestones] = useState<Row[]>([]);
  const [tasks, setTasks] = useState<Row[]>([]);
  const [error, setError] = useState("");
  const [revision, setRevision] = useState(0);
  const [form, setForm] = useState("");
  const executor =
    ["ADMIN", "MANAGER"].includes(user.role) && p.status === "Active";
  const load = () => {
    setRevision((v) => v + 1);
    refreshParent();
  };
  useEffect(() => {
    Promise.all([
      api("/projects/" + p.id + "/milestones"),
      api("/projects/" + p.id + "/tasks"),
    ])
      .then(([m, t]) => {
        setMilestones(m);
        setTasks(t);
      })
      .catch((e) => setError(e.message));
  }, [p.id, revision]);
  async function act(path: string, method: string, body?: unknown) {
    try {
      await api(path, method, body);
      setForm("");
      load();
      notify("Project updated");
    } catch (e) {
      notify((e as Error).message);
    }
  }
  const tabs = [
    "Milestones",
    "Phases & Team",
    "Tasks",
    "Quality",
    ...(user.role !== "CUSTOMER" ? ["Materials"] : []),
    "Gallery",
    ...(user.role === "ADMIN" && p.status === "Completed"
      ? ["Public Portfolio"]
      : []),
    ...(user.role !== "CUSTOMER" ? ["Internal Team Chat"] : []),
    ...(user.role !== "WORKER" ? ["Customer Project Chat"] : []),
    ...(["ADMIN", "CUSTOMER"].includes(user.role) ? ["Payments"] : []),
  ];
  return (
    <>
      <button className="back-link" onClick={back}>
        ← All projects
      </button>
      <div className="page-heading">
        <div>
          <span className="eyebrow">{short(p.id)}</span>
          <h1>{p.title}</h1>
          <p>
            <MapPin size={15} />
            {p.location} · {date(p.start_date)} — {date(p.deadline)}
          </p>
        </div>
        <Badge>{p.status}</Badge>
      </div>
      <div className="notice">
        <strong>Current phase: </strong>
        {p.phases.find((ph: Row) => ph.status === "Active")
          ? (() => {
              const ph = p.phases.find((ph: Row) => ph.status === "Active");
              return `Phase ${ph.number} · ${ph.title} · ${ph.duration} days · Due ${date(ph.deadline)}`;
            })()
          : "No phase is currently active"}
      </div>
      <div className="project-summary">
        <div>
          <small>Verified progress</small>
          <strong>{p.progress}%</strong>
        </div>
        <div className="progress-track">
          <div style={{ width: p.progress + "%" }} />
        </div>
        <div>
          <small>Manager</small>
          <strong>{p.manager_name || "Assigned project manager"}</strong>
        </div>
        <div>
          <small>Team</small>
          <strong>{p.worker_ids.length} workers</strong>
        </div>
        <div>
          <small>Phases</small>
          <strong>{p.phases.length}</strong>
        </div>
      </div>
      <div className="tabs">
        {tabs.map((t) => (
          <button
            key={t}
            className={tab === t ? "active" : ""}
            onClick={() => {
              setTab(t);
              setForm("");
            }}
          >
            {t}
          </button>
        ))}
      </div>
      {user.role === "ADMIN" && p.status !== "Completed" && (
        <Button
          secondary
          onClick={async () => {
            const note = prompt(
              "Reason for " +
                (p.status === "On Hold" ? "resuming" : "pausing") +
                " this project",
            );
            if (!note) return;
            await act("/projects/" + p.id + "/status", "PATCH", {
              status: p.status === "On Hold" ? "Active" : "On Hold",
              note,
            });
          }}
        >
          {p.status === "On Hold" ? "Resume project" : "Place project on hold"}
        </Button>
      )}
      {error && <div className="error">{error}</div>}
      {tab === "Milestones" && (
        <>
          <div className="block-heading">
            <h2>The way forward</h2>
            {executor && (
              <Button
                secondary
                onClick={() => setForm(form ? "" : "milestone")}
              >
                <Plus size={16} />
                Add milestone
              </Button>
            )}
          </div>
          {form === "milestone" && (
            <article className="card">
              <Form
                onSubmit={async (f) => {
                  await api("/projects/" + p.id + "/milestones", "POST", {
                    ...obj(f),
                    phase: Number(f.get("phase")),
                  });
                  setForm("");
                  load();
                }}
              >
                <Field label="Milestone title" name="title" />
                <Select
                  label="Phase"
                  name="phase"
                  options={p.phases.map((v: Row) => ({
                    value: String(v.number),
                    label: `${v.number}. ${v.title}`,
                  }))}
                />
                <Field label="Deadline" name="deadline" type="date" />
                <Text label="Description" name="description" required={false} />
              </Form>
            </article>
          )}
          <div className="timeline">
            {milestones.length ? (
              milestones.map((m, i) => (
                <article className="card milestone" key={m.id}>
                  <span
                    className={
                      "step-number " + (m.progress === 100 ? "complete" : "")
                    }
                  >
                    {m.progress === 100 ? <Check size={17} /> : i + 1}
                  </span>
                  <div className="grow">
                    <div className="card-head">
                      <h3>{m.title}</h3>
                      <Badge>
                        {m.progress === 100
                          ? "Complete"
                          : m.progress
                            ? "In progress"
                            : "Planned"}
                      </Badge>
                    </div>
                    <p>{m.description}</p>
                    <small>
                      Phase {m.phase} · Due {date(m.deadline)}<br/>Last updated {date(m.updated_at||m.created_at)} by {m.last_updated_by_name||"Project team"}
                    </small>
                    <div className="progress-track">
                      <div style={{ width: m.progress + "%" }} />
                    </div>
                    {executor && (
                      <>
                        <details>
                          <summary>Edit milestone definition</summary>
                          <Form
                            submit="Update milestone"
                            onSubmit={async (f) => {
                              await api("/milestones/" + m.id, "PUT", {
                                ...obj(f),
                                phase: Number(f.get("phase")),
                              });
                              load();
                              notify("Milestone updated");
                            }}
                          >
                            <Field
                              name="title"
                              label="Milestone title"
                              defaultValue={m.title}
                            />
                            <Select
                              name="phase"
                              label="Phase"
                              defaultValue={m.phase}
                              options={p.phases.map((ph: Row) => ({
                                value: String(ph.number),
                                label: ph.title,
                              }))}
                            />
                            <Field
                              name="deadline"
                              label="Deadline"
                              type="date"
                              defaultValue={m.deadline}
                            />
                            <Text
                              name="description"
                              label="Description"
                              required={false}
                              defaultValue={m.description}
                            />
                          </Form>
                        </details>
                        <Button
                          secondary
                          onClick={() => {
                            const deadline = prompt(
                              "New milestone deadline (YYYY-MM-DD)",
                              m.deadline,
                            );
                            if (deadline)
                              act("/milestones/" + m.id, "PUT", {
                                title: m.title,
                                description: m.description || "",
                                phase: m.phase,
                                deadline,
                              });
                          }}
                        >
                          Update deadline
                        </Button>
                        <label>
                          Verified completion: {m.progress}%
                          <input
                            aria-label={"Progress for " + m.title}
                            type="range"
                            min={0}
                            max={100}
                            defaultValue={m.progress}
                            onMouseUp={(e) =>
                              act("/milestones/" + m.id, "PATCH", {
                                progress: Number(e.currentTarget.value),
                                publish: true,
                              })
                            }
                            onKeyUp={(e) => {
                              if (e.key.startsWith("Arrow"))
                                act("/milestones/" + m.id, "PATCH", {
                                  progress: Number(e.currentTarget.value),
                                  publish: true,
                                });
                            }}
                            onTouchEnd={(e) =>
                              act("/milestones/" + m.id, "PATCH", {
                                progress: Number(e.currentTarget.value),
                                publish: true,
                              })
                            }
                          />
                        </label>
                      </>
                    )}
                  </div>
                </article>
              ))
            ) : (
              <Empty
                title="A plan is taking shape"
                text="Admin or your assigned manager will define project milestones."
              />
            )}
          </div>
          {executor && p.status === "Active" && (
            <article className="card">
              <h3>Final quality review</h3>
              <p>
                Confirm all milestones and tasks are complete and the finished
                work passes your final quality check.
              </p>
              <Button
                onClick={() => {
                  if (
                    confirm(
                      "Confirm the final quality inspection passed and mark this project completed?",
                    )
                  )
                    act("/projects/" + p.id + "/complete", "POST");
                }}
              >
                Quality passed · Complete project <CheckCircle2 size={16} />
              </Button>
            </article>
          )}
          {user.role === "CUSTOMER" && p.status === "Completed" && (
            <article className="card">
              <h2>How did we do?</h2>
              <Form
                submit="Share feedback"
                onSubmit={async (f) => {
                  await api("/projects/" + p.id + "/feedback", "POST", {
                    rating: Number(f.get("rating")),
                    text: f.get("text"),
                  });
                  notify("Thank you for your feedback");
                }}
              >
                <Select
                  label="Rating"
                  name="rating"
                  options={["5", "4", "3", "2", "1"]}
                />
                <Text label="Your feedback" name="text" />
              </Form>
            </article>
          )}
        </>
      )}
      {tab === "Phases & Team" && (
        <>
          {user.role === "ADMIN" && executor && (
            <details className="card">
              <summary>Plan another phase</summary>
              <Form
                submit="Add planned phase"
                onSubmit={async (f) => {
                  await api("/projects/" + p.id + "/phases", "POST", {
                    number: Number(f.get("number")),
                    title: f.get("title"),
                    duration: Number(f.get("duration")),
                    start_date: f.get("start_date"),
                    deadline: f.get("deadline"),
                  });
                  load();
                  notify(
                    "Phase planned. Publish its quotation before activating it.",
                  );
                }}
              >
                <Field
                  name="number"
                  label="Phase number"
                  type="number"
                  min={2}
                  defaultValue={
                    Math.max(...p.phases.map((ph: Row) => ph.number)) + 1
                  }
                />
                <Field name="title" label="Phase name" />
                <Field
                  name="duration"
                  label="Estimated duration (days)"
                  type="number"
                  min={1}
                />
                <Field
                  name="start_date"
                  label="Planned start date"
                  type="date"
                  required={false}
                />
                <Field
                  name="deadline"
                  label="Expected end date"
                  type="date"
                  required={false}
                />
              </Form>
            </details>
          )}

          <div className="two-grid">
            {p.phases.map((ph: Row) => (
              <article className="card" key={ph.number}>
                <Badge>{ph.status}</Badge>
                <h2>
                  Phase {ph.number} · {ph.title}
                </h2>
                <p>
                  <Clock size={16} />
                  {ph.duration} days · Deadline {date(ph.deadline)}
                </p>
                {executor && (
                  <details>
                    <summary>Update phase schedule</summary>
                    <Form
                      submit="Update phase"
                      onSubmit={async (f) => {
                        await act(
                          "/projects/" + p.id + "/phases/" + ph.number,
                          "PATCH",
                          obj(f),
                        );
                      }}
                    >
                      <Field
                        label="Phase title"
                        name="title"
                        defaultValue={ph.title}
                      />
                      <Select
                        label="Status"
                        name="status"
                        defaultValue={ph.status}
                        options={["Planned", "Active", "Completed"]}
                      />
                      <Field
                        label="Start date"
                        name="start_date"
                        type="date"
                        defaultValue={ph.start_date}
                      />
                      <Field
                        label="Deadline"
                        name="deadline"
                        type="date"
                        defaultValue={ph.deadline}
                      />
                    </Form>
                  </details>
                )}
              </article>
            ))}
          </div>
          <article className="card">
            <h2>Project team</h2>
            <p>Manager: {p.manager_name || "Assigned manager"}</p>
            <div className="chips">
              {p.worker_ids.map((id: string) => (
                <Badge key={id}>
                  {p.team?.find((x: Row) => x.id === id)?.name || short(id)}
                </Badge>
              ))}
            </div>
            {executor && (
              <Form
                submit="Assign worker"
                onSubmit={async (f) => {
                  await act("/projects/" + p.id + "/workers", "POST", {
                    worker_id: f.get("worker_id"),
                  });
                }}
              >
                <Select
                  label="Available workers"
                  name="worker_id"
                  options={people
                    .filter(
                      (x) =>
                        x.role === "WORKER" &&
                        x.active &&
                        !p.worker_ids.includes(x.id),
                    )
                    .map((x) => ({ value: x.id, label: x.name }))}
                />
              </Form>
            )}
            {user.role === "ADMIN" && (
              <details>
                <summary>Reassign manager</summary>
                <Form
                  onSubmit={async (f) => {
                    await act(
                      "/projects/" + p.id + "/manager",
                      "PATCH",
                      obj(f),
                    );
                  }}
                >
                  <Select
                    label="Manager"
                    name="manager_id"
                    options={people
                      .filter((x) => x.role === "MANAGER" && x.active)
                      .map((x) => ({ value: x.id, label: x.name }))}
                  />
                </Form>
              </details>
            )}
          </article>
        </>
      )}
      {tab === "Tasks" && (
        <>
          <div className="block-heading">
            <h2>Work, one step at a time</h2>
            {executor && (
              <Button secondary onClick={() => setForm(form ? "" : "task")}>
                <Plus size={16} />
                Create task
              </Button>
            )}
          </div>
          {form === "task" && (
            <article className="card">
              <Form
                submit="Create task"
                onSubmit={async (f) => {
                  await api("/projects/" + p.id + "/tasks", "POST", {...obj(f),phase:Number(f.get("phase"))});
                  setForm("");
                  load();
                }}
              >
                <Field label="Task title" name="title" />
                <Select
                  name="phase"
                  label="Task phase"
                  options={p.phases
                    .filter((ph: Row) => ph.status !== "Completed")
                    .map((ph: Row) => ({
                      value: String(ph.number),
                      label: ph.title,
                    }))}
                />
                <Select
                  label="Assigned worker"
                  name="worker_id"
                  options={people
                    .filter((x) => p.worker_ids.includes(x.id))
                    .map((x) => ({ value: x.id, label: x.name }))}
                />
                <Field label="Deadline" name="deadline" type="date" />
                <Select
                  label="Priority"
                  name="priority"
                  options={["Normal", "High", "Urgent"]}
                />
                <Text
                  label="Instructions"
                  name="description"
                  required={false}
                />
              </Form>
            </article>
          )}
          <div className="stack">
            {tasks.length ? (
              tasks.map((t) => (
                <article className="card" key={t.id}>
                  <div className="card-head">
                    <h3>{t.title}</h3>
                    <Badge>{t.priority}</Badge>
                  </div>
                  <p>{t.description}</p>
                  <small>Due {date(t.deadline)}</small>
                  {executor && (
                    <div className="form-grid">
                      <label>
                        Assigned worker
                        <select
                          aria-label={"Assigned worker for " + t.title}
                          value={t.worker_id}
                          onChange={(e) =>
                            act("/tasks/" + t.id, "PUT", {
                              title: t.title,
                              description: t.description || "",
                              deadline: t.deadline,
                              priority: t.priority,phase:t.phase||1,
                              worker_id: e.target.value,
                            })
                          }
                        >
                          {people
                            .filter((x) => p.worker_ids.includes(x.id))
                            .map((x) => (
                              <option key={x.id} value={x.id}>
                                {x.name}
                              </option>
                            ))}
                        </select>
                      </label>
                      <label>
                        Task deadline
                        <input
                          type="date"
                          value={t.deadline}
                          onChange={(e) => {
                            if (e.target.value)
                              act("/tasks/" + t.id, "PUT", {
                                title: t.title,
                                description: t.description || "",
                                deadline: e.target.value,
                                priority: t.priority,phase:t.phase||1,
                                worker_id: t.worker_id,
                              });
                          }}
                        />
                      </label>
                    </div>
                  )}
                  <div className="actions">
                    {user.role === "CUSTOMER" ? (
                      <Badge>{t.status}</Badge>
                    ) : (
                      <select
                        aria-label={"Status for " + t.title}
                        value={t.status}
                        onChange={(e) =>
                          act("/tasks/" + t.id, "PATCH", {
                            decision: e.target.value,
                          })
                        }
                      >
                        {["Pending", "In Progress", "Completed", "Blocked"].map(
                          (s) => (
                            <option key={s}>{s}</option>
                          ),
                        )}
                      </select>
                    )}
                  </div>
                </article>
              ))
            ) : (
              <Empty
                title="No tasks yet"
                text="The project team will add assignments and instructions here."
              />
            )}
          </div>
        </>
      )}
      {["Materials", "Quality", "Gallery"].includes(tab) && (
        <ExecutionPanel project={p} user={user} tab={tab} notify={notify} />
      )}
      {tab.includes("Chat") && (
        <Chat
          project={p}
          user={user}
          channel={tab.startsWith("Internal") ? "internal" : "customer"}
          notify={notify}
        />
      )}
      {tab === "Public Portfolio" && (
        <PortfolioSettings project={p} notify={notify} />
      )}
      {tab === "Payments" && (
        <Finance project={p} admin={user.role === "ADMIN"} notify={notify} />
      )}
    </>
  );
}

function Chat({
  project,
  user,
  channel,
  notify,
}: {
  project: Row;
  user: Row;
  channel: string;
  notify: (s: string) => void;
}) {
  const [rows, setRows] = useState<Row[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [issue, setIssue] = useState(false);
  const load = () =>
    api("/projects/" + project.id + "/chat/" + channel)
      .then(setRows)
      .catch((e) => setError(e.message));
  useEffect(() => {
    load();
    const id = setInterval(load, 5000);
    return () => clearInterval(id);
  }, [project.id, channel]);
  return (
    <article className="card chat">
      <div className="chat-heading">
        <MessagesSquare size={20} />
        <div>
          <h2>
            {channel === "internal"
              ? "Internal Team Chat"
              : "Customer Project Chat"}
          </h2>
          <p>
            {channel === "internal"
              ? "Admin, assigned manager and workers · Progress photos stay private until reviewed."
              : "Customer, Admin and assigned manager · Verified project updates."}
          </p>
        </div>
        <span className="live-dot">Refreshes every 5s</span>
      </div>
      {error && <p className="error">{error}</p>}
      <div className="messages">
        {rows.length ? (
          rows.map((m) => (
            <div
              className={"message " + (m.sender_id === user.id ? "own" : "")}
              key={m.id}
            >
              <div className="message-meta">
                <strong>{m.sender_name}</strong>
                <small>
                  {m.role.toLowerCase()} ·{" "}
                  {new Date(m.created_at).toLocaleString()}
                </small>
              </div>
              {m.issue && <Badge>Work issue reported</Badge>}
              <p>{m.text}</p>
              {m.file_id && (
                <a
                  href={"/api/files/" + m.file_id}
                  target="_blank"
                  rel="noreferrer"
                >
                  <img
                    className="chat-photo"
                    src={"/api/files/" + m.file_id}
                    alt="Project attachment"
                  />
                </a>
              )}
              {m.verification && (
                <div>
                  <Badge>
                    {m.verification === "Pending"
                      ? "Pending verification"
                      : m.verification}
                  </Badge>
                  {m.published && <small> Shared with customer</small>}
                </div>
              )}
              {m.review_note && <small>Review: {m.review_note}</small>}
              {m.channel === "internal" &&
                m.verification === "Approved" &&
                !m.published &&
                ["ADMIN", "MANAGER"].includes(user.role) && (
                  <Button
                    onClick={async () => {
                      const text = prompt("Customer update", m.text);
                      if (text === null) return;
                      try {
                        await api("/messages/" + m.id + "/share", "POST", {
                          text,
                        });
                        await load();
                        notify("Verified evidence shared");
                      } catch (e) {
                        notify((e as Error).message);
                      }
                    }}
                  >
                    Share approved photo with customer
                  </Button>
                )}
              {m.verification === "Pending" &&
                ["ADMIN", "MANAGER"].includes(user.role) && (
                  <div className="actions">
                    <Button
                      onClick={async () => {
                        const text = prompt(
                          "Accompanying customer update",
                          m.text,
                        );
                        if (text === null) return;
                        try {
                          await api("/messages/" + m.id + "/verify", "POST", {
                            approved: true,
                            share: true,
                            text,
                          });
                          await load();
                          notify("Verified photo shared with customer");
                        } catch (e) {
                          notify((e as Error).message);
                        }
                      }}
                    >
                      <Check size={15} />
                      Approve & share with customer
                    </Button>
                    <Button
                      secondary
                      onClick={async () => {
                        try {
                          await api("/messages/" + m.id + "/verify", "POST", {
                            approved: true,
                            share: false,
                          });
                          await load();
                          notify(
                            "Evidence approved; it remains internal until shared.",
                          );
                        } catch (e) {
                          notify((e as Error).message);
                        }
                      }}
                    >
                      Approve internally
                    </Button>
                    <Button
                      secondary
                      onClick={async () => {
                        const text = prompt(
                          "Correction required for this evidence",
                        );
                        if (text === null) return;
                        try {
                          await api("/messages/" + m.id + "/verify", "POST", {
                            approved: false,
                            text,
                          });
                          await load();
                        } catch (e) {
                          notify((e as Error).message);
                        }
                      }}
                    >
                      Needs correction
                    </Button>
                  </div>
                )}
            </div>
          ))
        ) : (
          <Empty
            title="Start the conversation"
            text="Messages and attachments remain saved with this project."
          />
        )}
      </div>
      <form
        className="composer"
        onSubmit={async (e) => {
          e.preventDefault();
          setBusy(true);
          setError("");
          try {
            const uploaded = file ? await upload(file) : null;
            await api("/projects/" + project.id + "/chat/" + channel, "POST", {
              text,
              file_id: uploaded?.id || null,
              issue,
            });
            setText("");
            setFile(null);
            setIssue(false);
            (e.target as HTMLFormElement).reset();
            await load();
          } catch (e) {
            setError((e as Error).message);
          } finally {
            setBusy(false);
          }
        }}
      >
        <label>
          Message
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder={
              channel === "internal"
                ? "Share instructions, progress or a work issue…"
                : "Ask a question or share a project update…"
            }
            rows={2}
          />
        </label>
        <div className="composer-tools">
          <label className="file-pick">
            <Upload size={16} />
            {file ? file.name : "Attach photograph"}
            <input
              aria-label="Attach photograph"
              type="file"
              accept="image/png,image/jpeg,image/webp"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
            />
          </label>
          {channel === "internal" && (
            <label className="checkbox">
              <input
                type="checkbox"
                checked={issue}
                onChange={(e) => setIssue(e.target.checked)}
              />
              Report a work issue
            </label>
          )}
          <Button type="submit" disabled={busy || (!text.trim() && !file)}>
            {busy ? "Sending…" : "Send message"}
            <ArrowUpRight size={16} />
          </Button>
        </div>
      </form>
    </article>
  );
}
