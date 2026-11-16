import { useEffect, useState } from "react";
import { api, Row } from "../api";
import { Empty } from "../components/ui";
export default function ServiceCatalogue({ path }: { path: string }) {
  const [rows, setRows] = useState<Row[]>([]),
    [error, setError] = useState(""),
    [loading, setLoading] = useState(true);
  useEffect(() => {
    api("/services")
      .then(setRows)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);
  const key = decodeURIComponent(path.split("/")[2] || "");
  const selected = key
    ? rows.filter(
        (s, i) =>
          s.id === key || s.name === key || (!s.id && String(i) === key),
      )
    : rows;
  return (
    <section className="section public-content">
      <span className="eyebrow">EXPERTISE IN EVERY FINISH</span>
      <h1>
        {key && selected[0] ? selected[0].name : "Services for every space."}
      </h1>
      <p>
        Careful preparation. Quality materials. A finish that feels like you.
      </p>
      {error && <p className="error">{error}</p>}
      {loading ? (
        <p role="status">Loading services…</p>
      ) : (
        <div className="three-grid">
          {selected.map((s, i) => (
            <article className="card" key={s.id || s.name}>
              {s.image_id ? (
                <img
                  className="gallery-photo"
                  src={"/api/public/services/" + s.id + "/image"}
                  alt={s.name}
                />
              ) : (
                <div className={"service-card service-" + (i % 4)}>
                  <div className="room-art">
                    <div />
                    <span />
                  </div>
                </div>
              )}
              <h2>{s.name}</h2>
              <p>
                {s.description ||
                  "An Admin site inspection defines materials, scope and the right finish for your space."}
              </p>
              <p>
                From site inspection and material selection to preparation and
                final quality checks, your project team manages every stage.
                Price and duration are confirmed through an official Admin
                quotation.
              </p>
              <a href={"#/services/" + (s.id || i)}>Service details ↗</a>
            </article>
          ))}
        </div>
      )}
      {!loading && !selected.length && (
        <Empty
          title="Service not available"
          text="Explore the current services, or contact the YEP team."
        />
      )}
    </section>
  );
}
