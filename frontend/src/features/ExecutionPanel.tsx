import { useEffect, useState } from "react";
import { api, date, Row } from "../api";
import { Badge, Empty, Field, Form, obj, Select, Text } from "../components/ui";

export default function ExecutionPanel({
  project,
  user,
  tab,
  notify,
}: {
  project: Row;
  user: Row;
  tab: string;
  notify: (s: string) => void;
}) {
  const [rows, setRows] = useState<Row[]>([]);
  const [version, setVersion] = useState(0);
  const [error, setError] = useState("");
  const executor =
    ["ADMIN", "MANAGER"].includes(user.role) && project.status !== "Completed";
  useEffect(() => {
    setRows([]);
    setError("");
    const suffix =
      tab === "Materials"
        ? "materials"
        : tab === "Quality"
          ? "quality"
          : "chat/" + (user.role === "WORKER" ? "internal" : "customer");
    api("/projects/" + project.id + "/" + suffix)
      .then((r) =>
        setRows(tab === "Gallery" ? r.filter((m: Row) => m.file_id) : r),
      )
      .catch((e) => setError(e.message));
  }, [tab, project.id, version]);
  return (
    <>
      {error && <p className="error">{error}</p>}
      {tab === "Gallery" ? (
        <div className="three-grid">
          {rows.map((r) => (
            <article className="card" key={r.id}>
              <a
                href={"/api/files/" + r.file_id}
                target="_blank"
                rel="noreferrer"
              >
                <img
                  className="gallery-photo"
                  src={"/api/files/" + r.file_id}
                  alt={r.text || "Project photograph"}
                />
              </a>
              <p>{r.text}</p>
              <small>
                {date(r.created_at)} · {r.sender_name}
              </small>
              {r.verification && <Badge>{r.verification}</Badge>}
            </article>
          ))}
          {rows.length === 0 && (
            <Empty
              title="Your project gallery"
              text="Photographs shared in your permitted project chat will appear here."
            />
          )}
        </div>
      ) : (
        <>
          <article className="card">
            <h2>
              {tab === "Materials"
                ? "Material requirements"
                : "Quality inspection history"}
            </h2>
            {rows.map((r) => (
              <div className="record-row" key={r.id}>
                <Badge>
                  {tab === "Materials"
                    ? r.status
                    : r.passed
                      ? "Passed"
                      : "Needs correction"}
                </Badge>
                <h3>{r.name || r.title}</h3>
                <p>
                  {tab === "Materials"
                    ? `${r.quantity} ${r.unit} · ${r.notes}`
                    : `Defects: ${r.defects || "None recorded"}. Corrective action: ${r.corrective_action || "None required"}`}
                </p>
                <small>{date(r.created_at)}</small>
              </div>
            ))}
            {rows.length === 0 && <p className="muted">No records yet.</p>}
          </article>
          {executor && (
            <article className="card">
              <h2>
                {tab === "Materials"
                  ? "Add material requirement"
                  : "Record quality inspection"}
              </h2>
              <Form
                key={tab + "-" + version}
                submit="Save record"
                onSubmit={async (f) => {
                  const data =
                    tab === "Materials"
                      ? { ...obj(f), quantity: Number(f.get("quantity")) }
                      : { ...obj(f), passed: f.get("passed") === "true" };
                  await api(
                    "/projects/" +
                      project.id +
                      "/" +
                      (tab === "Materials" ? "materials" : "quality"),
                    "POST",
                    data,
                  );
                  setVersion((v) => v + 1);
                  notify("Record saved");
                }}
              >
                {tab === "Materials" ? (
                  <>
                    <Field name="name" label="Material" />
                    <Field
                      name="quantity"
                      label="Quantity"
                      type="number"
                      min={0.01}
                      step="0.01"
                    />
                    <Field name="unit" label="Unit" />
                    <Select
                      name="status"
                      label="Availability"
                      options={["Required", "Available", "Shortage"]}
                    />
                    <Text name="notes" label="Notes" required={false} />
                  </>
                ) : (
                  <>
                    <Field
                      name="title"
                      label="Inspection checklist / area reviewed"
                    />
                    <Select
                      name="passed"
                      label="Result"
                      options={[
                        { value: "false", label: "Needs correction" },
                        { value: "true", label: "Passed" },
                      ]}
                    />
                    <Text
                      name="defects"
                      label="Defects found"
                      required={false}
                    />
                    <Text
                      name="corrective_action"
                      label="Corrective action"
                      required={false}
                    />
                  </>
                )}
              </Form>
            </article>
          )}
        </>
      )}
    </>
  );
}
