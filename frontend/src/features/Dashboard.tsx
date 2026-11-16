import SystemSettings from "./SystemSettings";
import WorkspaceInsights from "./WorkspaceInsights";
import ExecutionReports from "./ExecutionReports";
import {
  ArrowRight,
  ArrowUpRight,
  Bell,
  CheckCircle2,
  ChevronRight,
  Clock,
  FileText,
  FolderKanban,
  Home,
  Layers,
  LayoutDashboard,
  LogOut,
  MapPin,
  Menu,
  Paintbrush,
  Plus,
  Sparkles,
  Upload,
  Users,
  Wallet,
  X,
} from "lucide-react";
import React, { useEffect, useState } from "react";
import { api, date, money, Row, short, upload } from "../api";
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
import { serviceNames } from "../constants";
import AIStudio from "./AIStudio";
import AdminPanel from "./AdminPanel";
import Finance from "./Finance";
import ProjectDetail from "./Project";
import QuoteBuilder from "./QuoteBuilder";

export default function Dashboard({
  user,
  setUser,
  go,
  notify,
}: {
  user: Row;
  setUser: (u: Row | null) => void;
  go: (s: string) => void;
  notify: (s: string) => void;
}) {
  const [tab, setTab] = useState(
    sessionStorage.getItem("newRequest") === "yes" && user.role === "CUSTOMER"
      ? "New Request"
      : "Overview",
  );
  const [mobile, setMobile] = useState(false);
  const [projects, setProjects] = useState<Row[]>([]);
  const [requests, setRequests] = useState<Row[]>([]);
  const [quotes, setQuotes] = useState<Row[]>([]);
  const [people, setPeople] = useState<Row[]>([]);
  const [activeServices, setActiveServices] = useState(serviceNames);
  useEffect(() => {
    api("/services")
      .then((rows: Row[]) => {
        setActiveServices(rows.map((s) => s.name));
      })
      .catch(() => {});
  }, []);
  const [notes, setNotes] = useState<Row[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Row | null>(null);
  const [modal, setModal] = useState<{
    title: string;
    content: React.ReactNode;
  } | null>(null);
  const [version, setVersion] = useState(0);
  const isAdmin = user.role === "ADMIN",
    isCustomer = user.role === "CUSTOMER",
    executor = isAdmin || user.role === "MANAGER";
  const financeAllowed = isAdmin || isCustomer;
  const refresh = () => setVersion((v) => v + 1);
  useEffect(() => {
    sessionStorage.removeItem("newRequest");
  }, []);
  useEffect(() => {
    let live = true;
    if (version === 0) setLoading(true);
    (async () => {
      try {
        const [p, n, r, q, pe] = await Promise.all([
          api("/projects"),
          api("/notifications"),
          financeAllowed ? api("/requests") : Promise.resolve([]),
          financeAllowed ? api("/quotes") : Promise.resolve([]),
          executor ? api("/users") : Promise.resolve([]),
        ]);
        if (live) {
          setProjects(p);
          setNotes(n);
          setRequests(r);
          setQuotes(q);
          setPeople(pe);
          setError("");
        }
      } catch (e) {
        if (live) setError((e as Error).message);
      } finally {
        if (live) setLoading(false);
      }
    })();
    return () => {
      live = false;
    };
  }, [version]);
  const done = (message = "Saved successfully") => {
    setModal(null);
    notify(message);
    refresh();
  };
  const act = async (path: string, method = "POST", body?: unknown) => {
    try {
      await api(path, method, body);
      done();
    } catch (e) {
      notify((e as Error).message);
    }
  };
  const navigation = [
    { name: "Overview", icon: LayoutDashboard },
    ...(financeAllowed ? [{ name: "Requests", icon: FileText }] : []),
    ...(isCustomer ? [{ name: "New Request", icon: Plus }] : []),
    { name: "Projects", icon: FolderKanban },
    ...(financeAllowed
      ? [{ name: "Quotations & Payments", icon: Wallet }]
      : []),
    { name: "Notifications", icon: Bell },
    ...(isAdmin
      ? [
          { name: "Team", icon: Users },
          { name: "Activity", icon: Clock },
          { name: "Reports", icon: Layers },
          { name: "Services", icon: Paintbrush },
          { name: "System Settings", icon: Users },
          { name: "Customers & Enquiries", icon: Users },
        ]
      : []),
    ...(user.role === "MANAGER"
      ? [{ name: "Execution Reports", icon: Layers }]
      : []),
    { name: "Profile", icon: Users },
  ];
  const selectTab = (s: string) => {
    if (s === "Notifications") refresh();
    setTab(s);
    setSelected(null);
    setMobile(false);
  };
  const inspection = (r: Row) =>
    setModal({
      title: "Record Admin site inspection",
      content: (
        <Form
          submit="Save inspection"
          onSubmit={async (f) => {
            const ids = [];
            for (const v of f.getAll("photos"))
              if (v instanceof File && v.size) ids.push((await upload(v)).id);
            await api("/requests/" + r.id + "/inspection", "POST", {
              date: f.get("date"),
              measurements: f.get("measurements"),
              notes: f.get("notes"),
              materials: f.get("materials"),
              completed: f.get("completed") === "true",
              file_ids: ids,
            });
            done("Inspection saved");
          }}
          close={() => setModal(null)}
        >
          <Field label="Inspection date" name="date" type="date" />
          <Select
            label="Status"
            name="completed"
            options={[
              { value: "false", label: "Scheduled" },
              { value: "true", label: "Completed" },
            ]}
          />
          <Text label="Site measurements" name="measurements" />
          <Text label="Inspection findings" name="notes" />
          <Text
            label="Material requirements"
            name="materials"
            required={false}
          />
          <label className="wide">
            Inspection photos
            <input
              type="file"
              name="photos"
              accept="image/png,image/jpeg,image/webp"
              multiple
            />
          </label>
        </Form>
      ),
    });
  const quotation = (r: Row) =>
    setModal({
      title: "Prepare phase quotation",
      content: (
        <QuoteBuilder
          request={r}
          onDone={() =>
            done("Draft saved. Publish it from Quotations & Payments.")
          }
          close={() => setModal(null)}
        />
      ),
    });
  const createProject = (q: Row) =>
    setModal({
      title: "Create project from accepted Phase 1",
      content: (
        <Form
          submit="Create project"
          close={() => setModal(null)}
          onSubmit={async (f) => {
            await api("/projects", "POST", { ...obj(f), quote_id: q.id });
            done("Project created with two project chats");
          }}
        >
          <Field label="Project title" name="title" defaultValue={q.title} />
          <Select
            name="manager_id"
            label="Project manager"
            options={people
              .filter((p) => p.role === "MANAGER" && p.active)
              .map((p) => ({ value: p.id, label: p.name }))}
          />
          <Field label="Start date" name="start_date" type="date" />
          <Field label="Deadline" name="deadline" type="date" />
        </Form>
      ),
    });
  return (
    <div className="app-shell">
      <aside className={mobile ? "sidebar open" : "sidebar"}>
        <a className="logo" href="#/">
          yep<span>®</span>
        </a>
        <div className="workspace-tag">
          {user.role === "ADMIN"
            ? "Owner / Admin"
            : user.role.charAt(0) + user.role.slice(1).toLowerCase()}{" "}
          workspace
        </div>
        <div className="nav-caption">WORKSPACE</div>
        {navigation.map((n) => (
          <button
            key={n.name}
            className={"side-link " + (tab === n.name ? "active" : "")}
            onClick={() => selectTab(n.name)}
          >
            <n.icon size={18} />
            {n.name}
            {n.name === "Notifications" && notes.length > 0 && (
              <small>{notes.filter((n) => !n.read).length}</small>
            )}
          </button>
        ))}
        {isCustomer && (
          <>
            <div className="nav-caption ai-caption">
              DESIGN & DISCOVERY <Sparkles size={12} />
            </div>
            {[
              "AI Design Studio",
              "AI Design Assistant",
              "AI Cost Estimator",
              "Smart Recommendations",
              "AI Project Insights",
            ].map((n) => (
              <button
                className={"side-link " + (tab === n ? "active" : "")}
                key={n}
                onClick={() => selectTab(n)}
              >
                <Sparkles size={17} />
                {n}
              </button>
            ))}
          </>
        )}
        <div className="sidebar-bottom">
          <div className="help-card">
            <Layers size={20} />
            <strong>Every detail, connected.</strong>
            <p>Your project team is a conversation away.</p>
            <button onClick={() => selectTab("Projects")}>
              View your projects <ArrowRight size={14} />
            </button>
          </div>
          <button className="side-link" onClick={() => go("/")}>
            <Home size={18} />
            Public website
            <ArrowUpRight size={14} />
          </button>
          <button
            className="side-link"
            onClick={async () => {
              await api("/auth/logout", "POST");
              setUser(null);
              go("/login");
            }}
          >
            <LogOut size={18} />
            Sign out
          </button>
        </div>
      </aside>
      <main className="workspace">
        <header className="topbar">
          <button
            className="mobile-menu"
            onClick={() => setMobile(!mobile)}
            aria-label="Toggle sidebar"
          >
            <Menu />
          </button>
          <span>
            Workspace <ChevronRight size={14} />{" "}
            <strong>{selected ? "Project details" : tab}</strong>
          </span>
          <div className="top-right">
            <button
              aria-label="Notifications"
              onClick={() => selectTab("Notifications")}
            >
              <Bell size={19} />
              {notes.length > 0 && <i />}
            </button>
            <div className="user-avatar">
              {user.name
                .split(" ")
                .map((s: string) => s[0])
                .slice(0, 2)
                .join("")}
            </div>
            <div>
              <strong>{user.name}</strong>
              <small>
                {user.role === "ADMIN"
                  ? "Owner / Admin"
                  : user.role.toLowerCase()}
              </small>
            </div>
          </div>
        </header>
        <div className="workspace-body">
          {error ? (
            <div className="error">
              {error}
              <Button secondary onClick={refresh}>
                Retry
              </Button>
            </div>
          ) : loading ? (
            <div className="loading-inline">Loading your workspace…</div>
          ) : selected ? (
            <ProjectDetail
              project={projects.find((p) => p.id === selected.id) || selected}
              user={user}
              people={people}
              notify={notify}
              refreshParent={refresh}
              back={() => setSelected(null)}
            />
          ) : (
            <>
              <div className="page-heading">
                <div>
                  <span className="eyebrow">
                    {tab === "Overview"
                      ? "YOUR SPACE, IN PROGRESS"
                      : "YEP WORKSPACE"}
                  </span>
                  <h1>
                    {tab === "Overview"
                      ? `Hello, ${user.name.split(" ")[0]}.`
                      : tab}
                  </h1>
                  <p>
                    {tab === "Overview"
                      ? "A little clarity for everything that’s taking shape."
                      : tab === "Projects"
                        ? "Every phase, every milestone, every detail."
                        : tab === "Requests"
                          ? "From your first idea to a carefully considered plan."
                          : ""}
                  </p>
                </div>
                {isCustomer && tab !== "New Request" && (
                  <Button onClick={() => selectTab("New Request")}>
                    <Plus size={17} /> New request
                  </Button>
                )}
              </div>
              {tab === "Overview" && (
                <>
                  <WorkspaceInsights role={user.role} />
                  <div className="stats-grid">
                    {[
                      [
                        financeAllowed ? requests.length : projects.length,
                        financeAllowed
                          ? "Project requests"
                          : "Assigned projects",
                        FileText,
                      ],
                      [
                        quotes.filter((q) => q.status === "Published").length,
                        financeAllowed
                          ? "Quotes to review"
                          : "Team notifications",
                        Clock,
                      ],
                      [
                        projects.filter((p) => p.status === "Active").length,
                        "Active projects",
                        FolderKanban,
                      ],
                      [
                        projects.filter((p) => p.status === "Completed").length,
                        "Completed projects",
                        CheckCircle2,
                      ],
                    ].map(([v, t, I], i) => {
                      const Icon = I as typeof FileText;
                      return (
                        <article className="stat" key={String(t)}>
                          <div>
                            <span>{String(t)}</span>
                            <Icon size={18} />
                          </div>
                          <strong>
                            {financeAllowed || i !== 1
                              ? String(v)
                              : notes.length}
                          </strong>
                          <small>
                            {
                              [
                                "Your journey starts here",
                                "Every next step, made clear",
                                "Good things are taking shape",
                                "Spaces ready for their next chapter",
                              ][i]
                            }
                          </small>
                        </article>
                      );
                    })}
                  </div>
                  <div className="overview-grid">
                    <div>
                      <div className="block-heading">
                        <h2>
                          Your projects <span>{projects.length}</span>
                        </h2>
                        <button onClick={() => selectTab("Projects")}>
                          View all <ArrowRight size={15} />
                        </button>
                      </div>
                      {projects.length ? (
                        projects
                          .slice(0, 3)
                          .map((p) => (
                            <ProjectCard
                              key={p.id}
                              p={p}
                              open={() => setSelected(p)}
                            />
                          ))
                      ) : (
                        <Empty
                          title="Make room for your next chapter"
                          text={
                            isCustomer
                              ? "Submit a request and your Admin will help turn your ideas into a plan."
                              : "Your assigned projects will appear here."
                          }
                        />
                      )}
                    </div>
                    <div>
                      <div className="block-heading">
                        <h2>Recent updates</h2>
                        <Bell size={16} />
                      </div>
                      <article className="card activity-list">
                        {notes.length ? (
                          notes.slice(0, 5).map((n) => (
                            <div className="activity-item" key={n.id}>
                              <span className="activity-dot" />
                              <div>
                                <p>{n.text}</p>
                                <small>{date(n.created_at)}</small>
                                {!n.read && (
                                  <button
                                    className="read-notification"
                                    onClick={() =>
                                      act(
                                        "/notifications/" + n.id + "/read",
                                        "PATCH",
                                      )
                                    }
                                  >
                                    Mark as read
                                  </button>
                                )}
                              </div>
                            </div>
                          ))
                        ) : (
                          <p className="muted">
                            You’re all caught up. New project updates will
                            appear here.
                          </p>
                        )}
                      </article>
                      <article className="inspiration">
                        <Sparkles size={22} />
                        <span className="eyebrow">A LITTLE INSPIRATION</span>
                        <h2>
                          Small changes.
                          <br />A whole new feeling.
                        </h2>
                        <p>
                          Explore the finishes and details that make a space
                          yours.
                        </p>
                        <button onClick={() => go("/services")}>
                          Explore services <ArrowUpRight size={16} />
                        </button>
                      </article>
                    </div>
                  </div>
                </>
              )}
              {tab === "New Request" && (
                <article className="card form-card">
                  <h2>Tell us what you have in mind.</h2>
                  <p>
                    Your request goes directly to Admin for review and a site
                    inspection.
                  </p>
                  <Form
                    submit="Submit project request"
                    onSubmit={async (f) => {
                      const ids = [];
                      for (const file of f.getAll("photos"))
                        if (file instanceof File && file.size)
                          ids.push((await upload(file)).id);
                      const data = obj(f);
                      delete data.photos;
                      await api("/requests", "POST", {
                        ...data,
                        area: Number(f.get("area")),
                        rooms: Number(f.get("rooms")),
                        file_ids: ids,
                      });
                      done("Request submitted to Admin");
                      setTab("Requests");
                    }}
                  >
                    <Select
                      label="Service"
                      name="service"
                      options={activeServices}
                    />
                    <Select
                      label="Property type"
                      name="property_type"
                      options={[
                        "Apartment",
                        "Independent house",
                        "Commercial space",
                        "Other",
                      ]}
                    />
                    <Field label="Property location" name="location" />
                    <Field
                      label="Area (sq ft)"
                      name="area"
                      type="number"
                      min={1}
                      step="0.01"
                    />
                    <Field
                      label="Number of rooms"
                      name="rooms"
                      type="number"
                      min={0}
                      defaultValue={1}
                    />
                    <Field
                      label="Preferred start date"
                      name="preferred_date"
                      type="date"
                      required={false}
                    />
                    <Text
                      label="Describe your project (at least 10 characters)"
                      name="description"
                    />
                    <Text
                      label="Additional requirements"
                      name="requirements"
                      required={false}
                    />
                    <label className="wide upload-zone">
                      <Upload size={22} /> Property photos
                      <input
                        type="file"
                        name="photos"
                        multiple
                        accept="image/png,image/jpeg,image/webp"
                      />
                      <small>PNG, JPEG or WebP · up to 10 MB each</small>
                    </label>
                  </Form>
                </article>
              )}
              {tab === "Requests" && (
                <div className="stack">
                  {requests.length ? (
                    requests.map((r) => (
                      <article className="card" key={r.id}>
                        <div className="card-head">
                          <div>
                            <small>
                              {short(r.id)} · {date(r.created_at)}
                            </small>
                            <h2>{r.service}</h2>
                          </div>
                          <Badge>{r.status}</Badge>
                        </div>
                        <p>{r.description}</p>
                        {isAdmin && (
                          <small>
                            Customer: {r.customer_name} · Preferred start:{" "}
                            {date(r.preferred_date)}
                          </small>
                        )}
                        <div className="detail-line">
                          <span>
                            <MapPin size={14} />
                            {r.location}
                          </span>
                          <span>{r.property_type}</span>
                          <span>
                            {r.area} sq ft · {r.rooms} rooms
                          </span>
                        </div>
                        <p className="muted">{r.requirements}</p>
                        <div className="actions">
                          {r.file_ids.map((id: string) => (
                            <a
                              className="file-link"
                              key={id}
                              href={"/api/files/" + id}
                              target="_blank"
                              rel="noreferrer"
                            >
                              Property photo <ArrowUpRight size={14} />
                            </a>
                          ))}
                        </div>
                        {isCustomer &&
                          r.status === "More Information Required" && (
                            <details>
                              <summary>Respond to Admin</summary>
                              <Form
                                submit="Send additional information"
                                onSubmit={async (f) => {
                                  const ids = [];
                                  for (const file of f.getAll("photos"))
                                    if (file instanceof File && file.size)
                                      ids.push((await upload(file)).id);
                                  await api(
                                    "/requests/" + r.id + "/reply",
                                    "POST",
                                    { text: f.get("text"), file_ids: ids },
                                  );
                                  done("Response sent to Admin");
                                }}
                              >
                                <Text label="Additional details" name="text" />
                                <label className="wide">
                                  Additional property photos
                                  <input
                                    type="file"
                                    name="photos"
                                    accept="image/png,image/jpeg,image/webp"
                                    multiple
                                  />
                                </label>
                              </Form>
                            </details>
                          )}
                        <InspectionStatus
                          key={r.id + ":" + r.status}
                          requestId={r.id}
                        />
                        {r.history?.map((h: Row, i: number) => (
                          <p className="muted" key={i}>
                            {date(h.date)} · {h.status}: {h.note}
                          </p>
                        ))}
                        {isAdmin &&
                          !projects.some((p) => p.request_id === r.id) && (
                            <details>
                              <summary>Review request</summary>
                              <Form
                                submit="Save review"
                                onSubmit={async (f) => {
                                  await api(
                                    "/requests/" + r.id + "/status",
                                    "PATCH",
                                    obj(f),
                                  );
                                  done("Review shared with customer");
                                }}
                              >
                                <Select
                                  name="status"
                                  label="Review status"
                                  options={[
                                    "Under Review",
                                    "More Information Required",
                                    "Rejected",
                                  ]}
                                />
                                <Text
                                  name="note"
                                  label="Customer-visible response"
                                />
                              </Form>
                            </details>
                          )}
                        {isAdmin && (
                          <div className="actions">
                            <Button secondary onClick={() => inspection(r)}>
                              Record inspection
                            </Button>
                            <Button onClick={() => quotation(r)}>
                              Prepare phase quotation <Plus size={15} />
                            </Button>
                          </div>
                        )}
                      </article>
                    ))
                  ) : (
                    <Empty
                      title="No requests yet"
                      text="New project requests will appear here."
                    />
                  )}
                </div>
              )}
              {tab === "Projects" && (
                <div className="projects-grid">
                  {projects.length ? (
                    projects.map((p) => (
                      <ProjectCard
                        p={p}
                        key={p.id}
                        open={() => setSelected(p)}
                      />
                    ))
                  ) : (
                    <Empty
                      title="No assigned projects yet"
                      text="Projects appear here after Admin creates and assigns them."
                    />
                  )}
                </div>
              )}
              {tab === "Quotations & Payments" && (
                <>
                  <div className="stack">
                    {quotes.length ? (
                      quotes.map((q) => (
                        <article className="card" key={q.id}>
                          <div className="card-head">
                            <div>
                              <small>
                                {q.number} · Revision {q.revision}
                              </small>
                              <h2>
                                Phase {q.phase} · {q.title}
                              </h2>
                            </div>
                            <Badge>{q.status}</Badge>
                          </div>
                          <p>{q.description}</p>
                          <div className="quote-amount">
                            <strong>{money(q.amount_cents)}</strong>
                            <span>
                              <Clock size={15} />
                              {q.duration} days
                            </span>
                          </div>
                          {q.items?.length > 0 && (
                            <div className="table-wrap">
                              <table>
                                <thead>
                                  <tr>
                                    <th>Description</th>
                                    <th>Category</th>
                                    <th>Quantity</th>
                                    <th>Unit price</th>
                                    <th>Total</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {q.items.map((item: Row, i: number) => (
                                    <tr key={i}>
                                      <td>{item.description}</td>
                                      <td>{item.category}</td>
                                      <td>
                                        {item.quantity} {item.unit}
                                      </td>
                                      <td>{money(item.unit_price_cents)}</td>
                                      <td>{money(item.total_cents)}</td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                              <p className="muted">
                                Tax: {q.tax_percent}% · Discount:{" "}
                                {money(q.discount_cents || 0)}
                              </p>
                            </div>
                          )}
                          <p className="muted">Terms: {q.terms}</p>
                          {q.decided_at && (
                            <small>
                              Customer decision recorded {date(q.decided_at)}
                            </small>
                          )}
                          <div className="actions">
                            <a
                              className="btn secondary"
                              href={"/api/files/" + q.pdf_id}
                              target="_blank"
                              rel="noreferrer"
                            >
                              <FileText size={16} /> Open quotation PDF
                            </a>
                            {isAdmin && q.status === "Draft" && (
                              <Button
                                secondary
                                onClick={() =>
                                  setModal({
                                    title: "Edit quotation draft",
                                    content: (
                                      <QuoteBuilder
                                        request={{ id: q.request_id }}
                                        quote={q}
                                        onDone={() => done("Draft updated")}
                                        close={() => setModal(null)}
                                      />
                                    ),
                                  })
                                }
                              >
                                Edit draft
                              </Button>
                            )}
                            {isAdmin && q.status === "Draft" && (
                              <Button
                                onClick={() =>
                                  act("/quotes/" + q.id + "/publish")
                                }
                              >
                                Publish to customer
                              </Button>
                            )}
                            {isCustomer &&
                              q.status === "Published" &&
                              [
                                "Accepted",
                                "Rejected",
                                "Revision Requested",
                              ].map((s) => (
                                <Button
                                  secondary={s !== "Accepted"}
                                  key={s}
                                  onClick={() =>
                                    act(
                                      "/quotes/" + q.id + "/decision",
                                      "POST",
                                      { decision: s },
                                    )
                                  }
                                >
                                  {s === "Accepted"
                                    ? "Accept quotation"
                                    : s === "Rejected"
                                      ? "Reject"
                                      : "Request revision"}
                                </Button>
                              ))}
                            {isAdmin &&
                              q.phase === 1 &&
                              q.status === "Accepted" &&
                              !projects.some(
                                (p) => p.request_id === q.request_id,
                              ) && (
                                <Button onClick={() => createProject(q)}>
                                  Create project <ArrowRight size={16} />
                                </Button>
                              )}
                          </div>
                        </article>
                      ))
                    ) : (
                      <Empty
                        title="No quotations yet"
                        text="Admin publishes quotations after completing the site inspection."
                      />
                    )}
                  </div>
                  <div className="block-heading">
                    <h2>Project payment summaries</h2>
                  </div>
                  <div className="stack">
                    {projects.map((p) => (
                      <Finance
                        key={p.id}
                        project={p}
                        admin={isAdmin}
                        notify={notify}
                      />
                    ))}
                  </div>
                </>
              )}
              {tab === "Notifications" && (
                <article className="card activity-list">
                  {notes.length ? (
                    notes.map((n) => (
                      <div className="activity-item" key={n.id}>
                        <span className="activity-dot" />
                        <div>
                          <p>{n.text}</p>
                          <small>{date(n.created_at)}</small>
                          {!n.read && (
                            <button
                              className="read-notification"
                              onClick={() =>
                                act("/notifications/" + n.id + "/read", "PATCH")
                              }
                            >
                              Mark as read
                            </button>
                          )}
                        </div>
                      </div>
                    ))
                  ) : (
                    <Empty
                      title="All caught up"
                      text="Your notifications will appear here."
                    />
                  )}
                </article>
              )}
              {tab === "Team" && (
                <>
                  <div className="block-heading">
                    <h2>Managers & workers</h2>
                    <Button
                      onClick={() =>
                        setModal({
                          title: "Add team member",
                          content: (
                            <Form
                              submit="Create employee"
                              close={() => setModal(null)}
                              onSubmit={async (f) => {
                                await api("/users", "POST", obj(f));
                                done();
                              }}
                            >
                              <Field name="name" label="Full name" />
                              <Field name="email" label="Email" type="email" />
                              <Field
                                name="phone"
                                label="Phone"
                                required={false}
                              />
                              <Select
                                name="role"
                                label="Role"
                                options={["MANAGER", "WORKER"]}
                              />
                              <Field
                                name="password"
                                label="Initial password (10+ characters)"
                                type="password"
                              />
                            </Form>
                          ),
                        })
                      }
                    >
                      <Plus size={16} /> Add employee
                    </Button>
                  </div>
                  <article className="card table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Name</th>
                          <th>Role</th>
                          <th>Status</th>
                          <th>Account</th>
                        </tr>
                      </thead>
                      <tbody>
                        {people.map((p) => (
                          <tr key={p.id}>
                            <td>{p.name}</td>
                            <td>{p.role}</td>
                            <td>
                              <Badge>{p.active ? "Active" : "Inactive"}</Badge>
                            </td>
                            <td>
                              <button
                                onClick={() =>
                                  setModal({
                                    title: "Edit employee details",
                                    content: (
                                      <Form
                                        submit="Save employee"
                                        close={() => setModal(null)}
                                        onSubmit={async (f) => {
                                          await api(
                                            "/users/" + p.id,
                                            "PATCH",
                                            obj(f),
                                          );
                                          done("Employee updated");
                                        }}
                                      >
                                        <Field
                                          name="name"
                                          label="Name"
                                          defaultValue={p.name}
                                        />
                                        <Field
                                          name="email"
                                          label="Email"
                                          type="email"
                                          defaultValue={p.email}
                                        />
                                        <Field
                                          name="phone"
                                          label="Phone"
                                          required={false}
                                          defaultValue={p.phone}
                                        /><Select name="role" label="Employee role" defaultValue={p.role} options={["MANAGER","WORKER"]}/>
                                      </Form>
                                    ),
                                  })
                                }
                              >
                                Edit details
                              </button>
                              <button
                                onClick={() =>
                                  act("/users/" + p.id + "/active", "PATCH", {
                                    decision: p.active ? "inactive" : "active",
                                  })
                                }
                              >
                                {p.active ? "Deactivate" : "Activate"}
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </article>
                </>
              )}
              {tab === "System Settings" && <SystemSettings notify={notify} />}
              {tab === "Execution Reports" && <ExecutionReports />}
              {tab === "Activity" && <Activity />}
              {["Reports", "Services", "Customers & Enquiries"].includes(
                tab,
              ) && <AdminPanel tab={tab} notify={notify} />}
              {tab === "Profile" && (
                <article className="card form-card">
                  <h2>Your profile</h2>
                  <p>
                    {user.email} · {user.role}
                  </p>
                  <Form
                    submit="Update profile"
                    onSubmit={async (f) => {
                      const u = await api("/profile", "PATCH", obj(f));
                      setUser(u);
                      notify("Profile updated");
                    }}
                  >
                    <Field label="Name" name="name" defaultValue={user.name} />
                    <Field
                      label="Email"
                      name="email"
                      type="email"
                      defaultValue={user.email}
                    />
                    <Field
                      label="Phone"
                      name="phone"
                      required={false}
                      defaultValue={user.phone}
                    />
                    <Field
                      label="Address"
                      name="address"
                      required={false}
                      defaultValue={user.address}
                    />
                    <Field
                      label="New password (optional, 10+ characters)"
                      name="password"
                      type="password"
                      required={false}
                    />
                  </Form>
                </article>
              )}
              {(tab.startsWith("AI ") || tab === "Smart Recommendations") && (
                <AIStudio tab={tab} projects={projects} />
              )}
            </>
          )}
        </div>
      </main>
      {modal && (
        <div className="modal-backdrop" onClick={() => setModal(null)}>
          <section
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-label={modal.title}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="card-head">
              <h2>{modal.title}</h2>
              <button aria-label="Close" onClick={() => setModal(null)}>
                <X />
              </button>
            </div>
            {modal.content}
          </section>
        </div>
      )}
    </div>
  );
}

function ProjectCard({ p, open }: { p: Row; open: () => void }) {
  return (
    <article className="project-card">
      <div className="project-visual">
        <div className="architectural-lines" />
        <Badge>{p.status}</Badge>
        <span>{p.title.charAt(0)}</span>
      </div>
      <div className="pad">
        <div className="card-head">
          <small>{short(p.id)}</small>
          <small>
            {p.phases.length} phase{p.phases.length !== 1 ? "s" : ""}
          </small>
        </div>
        <h2>{p.title}</h2>
        <p className="location">
          <MapPin size={14} />
          {p.location}
        </p>
        <div className="card-head">
          <small>Verified project progress</small>
          <strong>{p.progress}%</strong>
        </div>
        <div className="progress-track">
          <span style={{ width: p.progress + "%" }} />
        </div>
        <div className="card-head project-bottom">
          <span>
            <Clock size={14} /> {date(p.deadline)}
          </span>
          <button onClick={open}>
            View project <ArrowUpRight size={16} />
          </button>
        </div>
      </div>
    </article>
  );
}

function InspectionStatus({ requestId }: { requestId: string }) {
  const [data, setData] = useState<Row | null>(null);
  useEffect(() => {
    api("/requests/" + requestId + "/inspection")
      .then(setData)
      .catch(() => {});
  }, [requestId]);
  return data ? (
    <div className="inspection-info">
      <Badge>
        {data.completed ? "Inspection completed" : "Inspection scheduled"}
      </Badge>
      <span>
        {date(data.date)} · {data.measurements}
      </span>
      <p>{data.notes}</p>
      {data.file_ids?.map((id: string) => (
        <a key={id} href={"/api/files/" + id} target="_blank" rel="noreferrer">
          Inspection photo ↗{" "}
        </a>
      ))}
    </div>
  ) : (
    <p className="muted">Awaiting Admin inspection</p>
  );
}

function Activity() {
  const [rows, setRows] = useState<Row[]>([]);
  useEffect(() => {
    api("/activity").then(setRows);
  }, []);
  return (
    <article className="card table-wrap">
      <table>
        <thead>
          <tr>
            <th>Time</th>
            <th>Action</th>
            <th>Record</th>
            <th>User</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.id}>
              <td>{new Date(r.created_at).toLocaleString()}</td>
              <td>{r.action}</td>
              <td>{short(r.target)}</td>
              <td>{r.user_id.slice(0, 8)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </article>
  );
}
