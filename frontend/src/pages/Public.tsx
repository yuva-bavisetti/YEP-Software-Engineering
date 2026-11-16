import PublicGallery from "../features/PublicGallery";
import ServiceCatalogue from "../features/ServiceCatalogue";
import {
  ArrowRight,
  ArrowUpRight,
  CheckCircle2,
  MapPin,
  Menu,
  Paintbrush,
  ShieldCheck,
  Users,
} from "lucide-react";
import { useEffect, useState } from "react";
import { api, Row } from "../api";
import HouseScene from "../components/HouseScene";
import { Badge, Button, Field, Form, Text } from "../components/ui";
import { serviceNames } from "../constants";
export default function Public({
  path,
  go,
  user,
  notify,
}: {
  path: string;
  go: (s: string) => void;
  user: Row | null;
  notify: (s: string) => void;
}) {
  const [menu, setMenu] = useState(false);
  const [filter, setFilter] = useState("All");
  const [activeServices, setActiveServices] = useState(serviceNames);
  useEffect(() => {
    api("/services")
      .then((rows: Row[]) => {
        setActiveServices(rows.map((s) => s.name));
      })
      .catch(() => {});
  }, []);
  const nav = [
    "Home",
    "Services",
    "Projects",
    "About Us",
    "How It Works",
    "Contact",
  ];
  const paths = [
    "/",
    "/services",
    "/projects",
    "/about",
    "/how-it-works",
    "/contact",
  ];
  return (
    <div className="public">
      <header className="public-nav">
        <a href="#/" className="logo">
          yep<span>®</span>
        </a>
        <nav className={menu ? "open" : ""}>
          {nav.map((n, i) => (
            <a
              key={n}
              className={path === paths[i] ? "selected" : ""}
              href={"#" + paths[i]}
              onClick={() => setMenu(false)}
            >
              {n}
            </a>
          ))}
        </nav>
        <a className="login-link" href={user ? "#/dashboard" : "#/login"}>
          {user ? "My workspace" : "Log in"} <ArrowUpRight size={16} />
        </a>
        <button
          className="mobile-menu"
          aria-label="Toggle navigation"
          onClick={() => setMenu(!menu)}
        >
          <Menu />
        </button>
      </header>
      {path === "/" ? (
        <>
          <section className="hero">
            <div className="hero-copy">
              <span className="eyebrow">
                <span className="dot" /> BUILT AROUND YOU
              </span>
              <h1>
                Good spaces.
                <br />
                Great possibilities<span className="green">.</span>
              </h1>
              <p>
                Thoughtful renovations. Exceptional finishes.
                <br />
                We bring your vision to life, one detail at a time.
              </p>
              <div className="hero-proof">
                <div className="avatars">
                  <span>AK</span>
                  <span>MS</span>
                  <span>RJ</span>
                </div>
                <div>
                  <strong>Care in every corner</strong>
                  <small>One team, from idea to handover</small>
                </div>
              </div>
            </div>
            <div className="hero-scene">
              <div className="scene-label">
                <span className="dot" /> YOUR NEXT CHAPTER, REIMAGINED
              </div>
              <HouseScene />
              <div className="scene-bottom">
                <span className="tiny">
                  FROM A BLANK CANVAS
                  <br />
                  <strong>To a place called yours.</strong>
                </span>
                <Button
                  onClick={() => {
                    sessionStorage.setItem("newRequest", "yes");
                    go(user ? "/dashboard" : "/register");
                  }}
                >
                  Start New Project <ArrowUpRight size={17} />
                </Button>
              </div>
              <span className="scene-note">
                A little vision. A remarkable transformation.
              </span>
            </div>
          </section>
          <div className="trust-strip">
            <span>A BETTER WAY TO BUILD</span>
            <div>
              <ShieldCheck />
              Transparent at every step
            </div>
            <div>
              <Users />
              One connected team
            </div>
            <div>
              <CheckCircle2 />
              Quality, without compromise
            </div>
          </div>
          <section className="section">
            <div className="section-head">
              <div>
                <span className="eyebrow">WHAT WE DO</span>
                <h2>
                  Every detail.
                  <br />
                  Beautifully considered.
                </h2>
              </div>
              <div>
                <p>
                  Refresh a room or reimagine your entire home.
                  <br />
                  We have the craft to make it happen.
                </p>
                <a href="#/services">
                  Explore our services <ArrowUpRight size={16} />
                </a>
              </div>
            </div>
            <div className="service-grid">
              {activeServices.slice(0, 4).map((s, i) => (
                <a
                  href={"#/services/" + encodeURIComponent(s)}
                  className={"service-card service-" + i}
                  key={s}
                >
                  <div className="room-art">
                    <div />
                    <span />
                  </div>
                  <div className="service-title">
                    <span>
                      <small>0{i + 1}</small>
                      <h3>{s}</h3>
                    </span>
                    <ArrowUpRight />
                  </div>
                </a>
              ))}
            </div>
          </section>
          <section className="process-band">
            <span className="eyebrow">LESS STRESS. MORE POSSIBILITIES.</span>
            <h2>
              A clear path from
              <br />
              “what if” to “welcome home”.
            </h2>
            <div className="steps">
              {[
                "Tell us your vision",
                "We plan every detail",
                "Your space takes shape",
                "Enjoy the transformation",
              ].map((s, i) => (
                <div key={s}>
                  <span>0{i + 1}</span>
                  <h3>{s}</h3>
                  <p>
                    {
                      [
                        "Share your needs and a few photos.",
                        "Inspection, a clear quote, and your approval.",
                        "Follow milestones and verified updates.",
                        "A quality checked space, made for you.",
                      ][i]
                    }
                  </p>
                </div>
              ))}
            </div>
            <a href="#/how-it-works">
              See how it works <ArrowRight size={16} />
            </a>
          </section>
          <section className="section">
            <span className="eyebrow">WHY YEP</span>
            <h2>Your project. A shared commitment.</h2>
            <div className="three-grid">
              {[
                [
                  "01",
                  "Clarity from day one",
                  "Detailed phase quotations, clear durations, and a complete record of your verified payments.",
                ],
                [
                  "02",
                  "The right people, connected",
                  "Your customer, manager and craft team work together through dedicated project conversations.",
                ],
                [
                  "03",
                  "Progress you can trust",
                  "Every shared work photograph is reviewed by your project team before it reaches you.",
                ],
              ].map((a) => (
                <article className="card" key={a[0]}>
                  <small>{a[0]}</small>
                  <h3>{a[1]}</h3>
                  <p>{a[2]}</p>
                </article>
              ))}
            </div>
          </section>
          <PublicGallery preview/>
          <section className="contact-banner">
            <div>
              <span className="eyebrow">LET’S TALK POSSIBILITIES</span>
              <h2>Have a space in mind?</h2>
              <p>Tell us what you’re imagining. We’ll take it from there.</p>
            </div>
            <Button secondary onClick={() => go("/contact")}>
              Talk to our team <ArrowUpRight size={18} />
            </Button>
          </section>
        </>
      ) : path.startsWith("/services") ? (
        <ServiceCatalogue path={path}/>
      ) : path === "/projects" ? (
        <PublicGallery/>
      ) : path === "/about" ? (
        <section className="section public-content">
          <span className="eyebrow">MEET YEP</span>
          <h1>
            Built on care.
            <br />
            Finished with purpose.
          </h1>
          <p className="lead">
            YEP brings building finishing, renovation and maintenance into one
            connected workspace.
          </p>
          <div className="three-grid">
            {[
              [
                "Our approach",
                "We believe a well-managed project feels as good as its final result. Clear phases, verified work and thoughtful communication guide every step.",
              ],
              [
                "Our team",
                "Admins plan and inspect. Managers coordinate execution. Skilled workers bring the vision to life. Customers stay connected throughout.",
              ],
              [
                "This project",
                "YEP is a Software Engineering portfolio application, designed to demonstrate a complete locally hosted project management workflow.",
              ],
            ].map((a) => (
              <article className="card" key={a[0]}>
                <h2>{a[0]}</h2>
                <p>{a[1]}</p>
              </article>
            ))}
          </div>
        </section>
      ) : path === "/how-it-works" ? (
        <section className="section public-content">
          <span className="eyebrow">A CONNECTED JOURNEY</span>
          <h1>From first idea to final detail.</h1>
          <div className="timeline">
            {[
              "Submit your service request and property photos",
              "Admin reviews and completes a site inspection",
              "Admin publishes a detailed Phase 1 quotation",
              "You review the PDF, price and duration, then approve",
              "Admin creates the project and assigns your manager",
              "Your manager coordinates workers, tasks and milestones",
              "The team verifies progress and shares updates with you",
              "Admin publishes further phase quotations and records offline payments",
              "Quality review, completion and your feedback",
            ].map((s, i) => (
              <article className="card" key={s}>
                <span className="step-number">{i + 1}</span>
                <h3>{s}</h3>
              </article>
            ))}
          </div>
        </section>
      ) : (
        <section className="section public-content">
          <span className="eyebrow">LET’S MAKE ROOM FOR SOMETHING GOOD</span>
          <h1>We’re listening.</h1>
          <div className="two-grid">
            <div>
              <h2>Tell us about your space.</h2>
              <p>
                Use this form for a general enquiry. For a project quotation,
                create an account and submit a project request.
              </p>
              <p>
                <MapPin size={18} /> Site visits are scheduled with you after
                request review.
              </p>
              <small>Portfolio demonstration · local application</small>
            </div>
            <article className="card">
              <Form
                submit="Send enquiry"
                onSubmit={async (f) => {
                  await api("/enquiries", "POST", {
                    name: f.get("name"),
                    email: f.get("email"),
                    phone: f.get("phone"),
                    message: f.get("message"),
                  });
                  notify("Your enquiry has been saved.");
                }}
              >
                <Field label="Your name" name="name" />
                <Field label="Email" name="email" type="email" />
                <Field label="Phone" name="phone" required={false} />
                <Text label="How can we help?" name="message" />
              </Form>
            </article>
          </div>
        </section>
      )}
      <footer>
        <a className="logo" href="#/">
          yep<span>®</span>
        </a>
        <p>Spaces, thoughtfully transformed.</p>
        <span>
          © {new Date().getFullYear()} YEP · Software Engineering portfolio
        </span>
        <a href="#/contact">
          Let’s connect <ArrowUpRight size={16} />
        </a>
      </footer>
    </div>
  );
}
