import { useEffect, useState } from "react";
import { api, Row } from "../api";
import { Badge, Empty } from "../components/ui";
export default function PublicGallery({
  preview = false,
}: {
  preview?: boolean;
}) {
  const [rows, setRows] = useState<Row[]>([]),
    [category, setCategory] = useState("All"),
    [error, setError] = useState(""),
    [loading, setLoading] = useState(true);
  useEffect(() => {
    api("/public/projects")
      .then(setRows)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);
  const filtered = rows.filter(
    (p) => category === "All" || p.category === category,
  );
  return (
    <section className={"section " + (!preview ? "public-content" : "")}>
      <span className="eyebrow">COMPLETED & CONSIDERED</span>
      {preview ? (
        <h2>Spaces with a new story.</h2>
      ) : (
        <h1>Spaces with a new story.</h1>
      )}
      <p>
        Completed projects selected and published by the YEP team. Only verified
        photographs are included.
      </p>
      {error && <p className="error">{error}</p>}
      {loading ? (
        <p role="status">Loading completed projects…</p>
      ) : (
        <>
          <div className="tabs">
            {["All", ...new Set(rows.map((p) => p.category))].map((c) => (
              <button
                key={c}
                className={category === c ? "active" : ""}
                onClick={() => setCategory(c)}
              >
                {c}
              </button>
            ))}
          </div>
          <div className="three-grid">
            {(preview ? filtered.slice(0, 3) : filtered).map((p) => (
              <article className="service-card" key={p.id}>
                <img
                  className="portfolio-cover"
                  src={
                    "/api/public/projects/" +
                    p.project_id +
                    "/photos/" +
                    p.file_ids[0]
                  }
                  alt={p.title}
                />
                <div className="pad">
                  <Badge>{p.category}</Badge>
                  <h3>{p.title}</h3>
                  <p>{p.description}</p>
                  <div className="photo-strip">
                    {p.file_ids.slice(1).map((id: string) => (
                      <a
                        key={id}
                        href={
                          "/api/public/projects/" +
                          p.project_id +
                          "/photos/" +
                          id
                        }
                        target="_blank"
                        rel="noreferrer"
                      >
                        <img
                          src={
                            "/api/public/projects/" +
                            p.project_id +
                            "/photos/" +
                            id
                          }
                          alt={p.title + " completed detail"}
                        />
                      </a>
                    ))}
                  </div>
                  {p.feedback && (
                    <blockquote>
                      <span aria-label={p.feedback.rating + " out of 5 stars"}>
                        {"★".repeat(p.feedback.rating)}
                      </span>
                      <p>“{p.feedback.text}”</p>
                      <small>Verified project customer</small>
                    </blockquote>
                  )}
                </div>
              </article>
            ))}
          </div>
          {!filtered.length && (
            <Empty
              title="A gallery worth waiting for"
              text="Completed projects will appear after the team publishes their verified photographs."
            />
          )}
        </>
      )}
    </section>
  );
}
