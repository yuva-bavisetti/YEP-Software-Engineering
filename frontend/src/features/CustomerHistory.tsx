import { useEffect, useState } from "react";
import { api, date, Row } from "../api";
import { Badge } from "../components/ui";
export default function CustomerHistory({
  customerId,
}: {
  customerId: string;
}) {
  const [data, setData] = useState<Row | null>(null),
    [error, setError] = useState("");
  useEffect(() => {
    api("/admin/customers/" + customerId + "/history")
      .then(setData)
      .catch((e) => setError(e.message));
  }, [customerId]);
  if (error) return <p className="error">{error}</p>;
  if (!data) return <p>Loading customer history…</p>;
  return (
    <article className="card">
      <h2>{data.customer.name} · Project history</h2>
      <p>
        {data.requests.length} requests · {data.projects.length} projects ·{" "}
        {data.quotations.length} quotation revisions
      </p>
      {data.requests.map((r: Row) => (
        <p key={r.id}>
          {r.service} · {date(r.created_at)} <Badge>{r.status}</Badge>
        </p>
      ))}
      {data.projects.map((p: Row) => (
        <p key={p.id}>
          {p.title} · {p.progress}% complete <Badge>{p.status}</Badge>
        </p>
      ))}
    </article>
  );
}
