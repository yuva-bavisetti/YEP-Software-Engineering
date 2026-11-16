import CustomerHistory from "./CustomerHistory";
import { useEffect, useState } from "react";
import { api, date, money, Row, upload } from "../api";
import {
  Badge,
  Button,
  Empty,
  Field,
  Form,
  Select,
  Text,
} from "../components/ui";

export default function AdminPanel({
  tab,
  notify,
}: {
  tab: string;
  notify: (s: string) => void;
}) {
  const [data, setData] = useState<Row | null>(null);
  const [rows, setRows] = useState<Row[]>([]);
  const [version, setVersion] = useState(0);
  const [editing, setEditing] = useState<Row | null>(null);
  const [error, setError] = useState("");
  const [customerId, setCustomerId] = useState("");
  useEffect(() => {
    setData(null);
    setRows([]);
    setError("");
    (tab === "Reports"
      ? api("/admin/summary").then(setData)
      : tab === "Services"
        ? api("/admin/services").then(setRows)
        : Promise.all([api("/admin/customers"), api("/admin/enquiries")]).then(
            ([customers, enquiries]) => setData({ customers, enquiries }),
          )
    ).catch((e) => setError(e.message));
  }, [tab, version]);
  if (error) return <div className="error">{error}</div>;
  return tab === "Reports" ? (
    data ? (
      <>
        <div className="stats-grid">
          {[
            ["Customers", data.customers],
            ["Managers", data.managers],
            ["Workers", data.workers],
            ["Verified offline receipts", money(data.verified_receipts_cents)],
          ].map(([title, value]) => (
            <article className="stat" key={title}>
              <div>{title}</div>
              <strong style={{ fontSize: 24 }}>{value}</strong>
            </article>
          ))}
        </div>
        <article className="card">
          <h2>
            Approved quotation value: {money(data.approved_quotation_cents)}
          </h2>
          <p>
            Quotation values describe contracted work. Verified receipts
            represent recorded offline payments, net of reversals.
          </p>
        </article>
        <div className="two-grid">
          {[
            ["Requests by service", data.services],
            ["Project status", data.project_status],
            ["Employee workload", data.workload],
            ["Requests by month", data.request_months],
            ["Monthly project activity", data.project_months || {}],
            ["Quotation status", data.quotation_status || {}],
          ].map(([title, values]) => (
            <article className="card" key={title as string}>
              <h2>{title as string}</h2>
              {Object.entries(values).map(([name, value]) => (
                <div className="report-bar" key={name}>
                  <div className="card-head">
                    <small>{name}</small>
                    <strong>{String(value)}</strong>
                  </div>
                  <div
                    className="progress-track"
                    role="img"
                    aria-label={`${name}: ${value}`}
                  >
                    <div
                      style={{
                        width:
                          Math.max(
                            2,
                            (Number(value) /
                              Math.max(
                                1,
                                ...Object.values(values).map(Number),
                              )) *
                              100,
                          ) + "%",
                      }}
                    />
                  </div>
                </div>
              ))}
            </article>
          ))}
        </div>
      </>
    ) : (
      <p>Loading report…</p>
    )
  ) : tab === "Services" ? (
    <>
      <article className="card">
        <h2>{editing ? "Edit service" : "Add service"}</h2>
        <Form
          key={editing?.id || "new"}
          submit={editing ? "Save service" : "Add service"}
          close={editing ? () => setEditing(null) : undefined}
          onSubmit={async (f) => {
            const photo = f.get("image") as File;
            const image = photo?.size ? await upload(photo) : null;
            await api(
              "/services" + (editing ? "/" + editing.id : ""),
              editing ? "PUT" : "POST",
              {
                name: f.get("name"),
                description: f.get("description"),
                active: f.get("active") === "true",
                image_id: image?.id || editing?.image_id || null,
              },
            );
            setEditing(null);
            setVersion((v) => v + 1);
            notify("Service saved");
          }}
        >
          <Field
            label="Service name"
            name="name"
            defaultValue={editing?.name}
          />
          <Select
            name="active"
            label="Availability"
            options={
              editing?.active === false
                ? [
                    { value: "false", label: "Inactive" },
                    { value: "true", label: "Active" },
                  ]
                : [
                    { value: "true", label: "Active" },
                    { value: "false", label: "Inactive" },
                  ]
            }
          />
          <label className="wide">
            Service photograph
            <input
              type="file"
              name="image"
              accept="image/png,image/jpeg,image/webp"
            />
          </label>
          <Text
            label="Description"
            name="description"
            defaultValue={editing?.description}
          />
        </Form>
      </article>
      <div className="three-grid">
        {rows.map((r) => (
          <article className="card" key={r.id}>
            <Badge>{r.active ? "Active" : "Inactive"}</Badge>
            <h3>{r.name}</h3>
            <p>{r.description}</p>
            <Button secondary onClick={() => setEditing(r)}>
              Edit service
            </Button>
          </article>
        ))}
      </div>
    </>
  ) : data ? (
    <>
      <article className="card table-wrap">
        <h2>Customers</h2>
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Phone</th>
              <th>Address</th>
              <th>Account / history</th>
            </tr>
          </thead>
          <tbody>
            {data.customers.map((c: Row) => (
              <tr key={c.id}>
                <td>{c.name}</td>
                <td>{c.email}</td>
                <td>{c.phone || "—"}</td>
                <td>{c.address || "—"}</td>
                <td>
                  <button onClick={() => setCustomerId(c.id)}>
                    View history
                  </button>
                  <button
                    onClick={async () => {
                      try {
                        await api("/users/" + c.id + "/active", "PATCH", {
                          decision: c.active ? "inactive" : "active",
                        });
                        setVersion((v) => v + 1);
                        notify("Customer account updated");
                      } catch (e) {
                        notify((e as Error).message);
                      }
                    }}
                  >
                    {c.active ? "Deactivate" : "Activate"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </article>
      {customerId && <CustomerHistory customerId={customerId} />}
      <div className="block-heading">
        <h2>Contact enquiries</h2>
      </div>
      <div className="stack">
        {data.enquiries.map((e: Row) => (
          <article className="card" key={e.id}>
            <small>{date(e.created_at)}</small>
            <h3>
              {e.name} · {e.email}
            </h3>
            <p>{e.message}</p>
            <small>{e.phone}</small>
          </article>
        ))}
        {data.enquiries.length === 0 && (
          <Empty
            title="No enquiries yet"
            text="Submissions from the public contact form appear here."
          />
        )}
      </div>
    </>
  ) : (
    <p>Loading…</p>
  );
}
