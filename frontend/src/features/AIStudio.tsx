import {
  ArrowRight,
  ArrowUpRight,
  Home,
  Sparkles,
  Upload,
  Wallet,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Row } from "../api";
import { Badge, Button, Field, Form, Select, Text } from "../components/ui";
import { serviceNames } from "../constants";

export default function AIStudio({
  tab,
  projects,
}: {
  tab: string;
  projects: Row[];
}) {
  const [preview, setPreview] = useState("");
  const [color, setColor] = useState("#b5c4ab");
  const [style, setStyle] = useState("Warm minimal");
  const [notice, setNotice] = useState("");
  useEffect(
    () => () => {
      if (preview) URL.revokeObjectURL(preview);
    },
    [preview],
  );
  return (
    <div className="ai-studio">
      <div className="ai-banner">
        <Sparkles size={24} />
        <div>
          <strong>Your ideas, ready for what’s next.</strong>
          <p>
            Interface for future integration. No AI model is connected; your
            inputs are not sent to an external service.
          </p>
        </div>
        <Badge>Integration setup</Badge>
      </div>
      {tab === "AI Design Studio" ? (
        <div className="two-grid">
          <article className="card">
            <h2>Make room for your imagination.</h2>
            <p>Upload a room photograph and prepare your design preferences.</p>
            <label className="upload-zone">
              <Upload />
              <strong>Add a room or exterior photograph</strong>
              <input
                type="file"
                accept="image/*"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) setPreview(URL.createObjectURL(f));
                }}
              />
            </label>
            <label>
              Wall colour
              <input
                type="color"
                value={color}
                onChange={(e) => setColor(e.target.value)}
              />
            </label>
            <label>
              Design style
              <select value={style} onChange={(e) => setStyle(e.target.value)}>
                {[
                  "Warm minimal",
                  "Contemporary",
                  "Natural textures",
                  "Classic",
                  "Industrial",
                ].map((s) => (
                  <option key={s}>{s}</option>
                ))}
              </select>
            </label>
            <label>
              Floor finish
              <select>
                <option>Natural oak</option>
                <option>Porcelain tiles</option>
                <option>Stone</option>
              </select>
            </label>
            <Button
              onClick={() =>
                setNotice(
                  "Design generation requires a future image-processing provider. Your original image remains unchanged.",
                )
              }
            >
              Prepare design preview <Sparkles size={16} />
            </Button>
          </article>
          <article className="card preview-card">
            <span className="eyebrow">ORIGINAL PHOTOGRAPH</span>
            {preview ? (
              <img src={preview} alt="Your original room" />
            ) : (
              <div className="preview-empty">
                <Home size={60} />
                <p>Your space, a fresh perspective.</p>
              </div>
            )}
            <div className="palette">
              <span style={{ background: color }} />
              <div>
                <strong>{style}</strong>
                <small>
                  Selected palette · no image transformation applied
                </small>
              </div>
            </div>
          </article>
        </div>
      ) : tab === "AI Design Assistant" ? (
        <article className="card ai-assistant">
          <div className="assistant-mark">
            <Sparkles size={32} />
          </div>
          <h2>What would you like to explore?</h2>
          <p>
            Prepare a question about materials, finishes, colours or your
            renovation.
          </p>
          <div className="chips">
            {[
              "Help me choose wall colours",
              "Compare flooring materials",
              "What should I prepare for inspection?",
            ].map((s) => (
              <button
                key={s}
                onClick={() =>
                  setNotice(
                    "Selected question: " +
                      s +
                      ". An AI provider is not connected.",
                  )
                }
              >
                {s}
              </button>
            ))}
          </div>
          <label>
            Your question
            <textarea
              rows={4}
              placeholder="I’m renovating a bright living room…"
            />
          </label>
          <Button
            onClick={() =>
              setNotice(
                "No AI provider is connected. For project advice, message your manager in your project’s Customer Chat.",
              )
            }
          >
            Send when connected <ArrowUpRight size={16} />
          </Button>
        </article>
      ) : tab === "AI Cost Estimator" ? (
        <div className="two-grid">
          <article className="card">
            <h2>Plan your possibilities.</h2>
            <Form
              submit="Prepare estimate inputs"
              onSubmit={async () =>
                setNotice(
                  "Inputs prepared. An estimation model is not connected, so no estimate has been generated. Only an Admin quotation is official.",
                )
              }
            >
              <Field label="Area (sq ft)" name="area" type="number" min={1} />
              <Select label="Service" name="service" options={serviceNames} />
              <Select
                label="Finish grade"
                name="grade"
                options={["Standard", "Premium", "Luxury"]}
              />
              <Text
                label="Materials and requirements"
                name="requirements"
                required={false}
              />
            </Form>
          </article>
          <article className="card">
            <Wallet size={32} />
            <h2>Estimate workspace</h2>
            <p>
              Future estimates will appear here with their assumptions and
              scope. They will be indicative and separate from official
              Admin-approved quotations.
            </p>
            <Badge>No estimate generated</Badge>
          </article>
        </div>
      ) : tab === "Smart Recommendations" ? (
        <article className="card">
          <h2>A space that feels like you.</h2>
          <p>
            Set your preferences for future recommendations. Nothing is
            generated or personalised by AI yet.
          </p>
          <div className="form-grid">
            <Select
              label="Your space"
              name="space"
              options={["Living room", "Kitchen", "Bedroom", "Exterior"]}
            />
            <Select
              label="Your priority"
              name="priority"
              options={[
                "Durability",
                "Easy maintenance",
                "Natural materials",
                "Modern finish",
              ]}
            />
            <Field label="Preferred palette" name="palette" required={false} />
          </div>
          <Button
            onClick={() =>
              setNotice(
                "Preferences captured in this screen. A recommendation provider has not been connected.",
              )
            }
          >
            Prepare preferences <Sparkles size={16} />
          </Button>
        </article>
      ) : (
        <article className="card">
          <h2>A clearer view of your project.</h2>
          <p>
            Select a project to prepare a future progress summary. No AI
            summaries or photo comparisons are generated.
          </p>
          <Select
            label="Project"
            name="project"
            options={projects.map((p) => ({ value: p.id, label: p.title }))}
          />
          <div className="three-grid">
            {[
              "Progress summary",
              "Photo comparison",
              "Milestone explanation",
            ].map((s) => (
              <div className="empty" key={s}>
                <Sparkles size={23} />
                <h3>{s}</h3>
                <p>Ready for a future integration.</p>
              </div>
            ))}
          </div>
          <Button
            onClick={() =>
              setNotice(
                "Project insights require a future provider. View verified progress in Projects for current information.",
              )
            }
          >
            Prepare insights <ArrowRight size={16} />
          </Button>
        </article>
      )}
      {notice && (
        <div className="notice" role="status">
          {notice}
        </div>
      )}
    </div>
  );
}
