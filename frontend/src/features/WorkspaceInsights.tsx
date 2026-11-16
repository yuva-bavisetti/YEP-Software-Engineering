import { useEffect, useState } from "react";
import { api, date, Row } from "../api";
import { Badge } from "../components/ui";
export default function WorkspaceInsights({ role }: { role: string }) {
  const [data, setData] = useState<Row | null>(null),
    [error, setError] = useState("");
  useEffect(() => {
    let live = true;
    const load = () =>
      api("/dashboard")
        .then((d) => {
          if (live) setData(d);
        })
        .catch((e) => {
          if (live) setError(e.message);
        });
    load();
    const timer = setInterval(load, 15000);
    return () => {
      live = false;
      clearInterval(timer);
    };
  }, []);
  if (error) return <p className="error">{error}</p>;
  if (!data?.stats) return null;
  return (
    <article className="card insights">
      <h2>{role === "WORKER" ? "Your work, today" : "Workspace activity"}</h2>
      <div className="chips">
        <Badge>{data.stats.unread_notifications} unread notifications</Badge>
        {["WORKER", "MANAGER"].includes(role) && (
          <>
            <Badge>{data.stats.today_tasks} tasks due today or overdue</Badge>
            <Badge>
              {data.stats.pending_tasks} pending · {data.stats.completed_tasks}{" "}
              completed tasks
            </Badge>
          </>
        )}
      </div>
      <div className="two-grid">
        {data.current_phases.map((entry: Row) => (
          <div key={entry.project_id}>
            <h3>{entry.project_title}</h3>
            {entry.phase ? (
              <p>
                Current phase {entry.phase.number}: {entry.phase.title} ·{" "}
                {entry.phase.duration} days · Due {date(entry.phase.deadline)}
              </p>
            ) : (
              <p>No phase is currently active.</p>
            )}
          </div>
        ))}
      </div>
      {data.due_tasks.length > 0 && (
        <>
          <h3>Due work</h3>
          {data.due_tasks.map((t: Row) => (
            <p key={t.id}>
              {t.title} · {t.status} · {date(t.deadline)}
              <br />
              <small>{t.description}</small>
            </p>
          ))}
        </>
      )}
      {data.instructions?.length > 0 && (
        <>
          <h3>Manager & Admin instructions</h3>
          {data.instructions.map((m: Row) => (
            <p key={m.id}>
              {m.text}
              <br />
              <small>
                {m.sender_name} · {date(m.created_at)}
              </small>
            </p>
          ))}
        </>
      )}
    </article>
  );
}
