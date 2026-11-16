import { ArrowUpRight } from "lucide-react";
import { api, Row } from "../api";
import { Field, Form, obj } from "../components/ui";
export default function Auth({
  register,
  onDone,
  go,
}: {
  register: boolean;
  onDone: (u: Row) => void;
  go: (s: string) => void;
}) {
  return (
    <div className="auth">
      <div className="auth-story">
        <a className="logo" href="#/">
          yep<span>®</span>
        </a>
        <div>
          <span className="eyebrow">YOUR SPACE. OUR CRAFT.</span>
          <h1>
            A better space
            <br />
            starts here.
          </h1>
          <p>
            From the first idea to the final detail.
            <br />
            Your entire renovation, in one place.
          </p>
        </div>
        <small>Thoughtfully built. Beautifully finished.</small>
      </div>
      <div className="auth-form">
        <a href="#/" className="back">
          ← Back to YEP
        </a>
        <span className="eyebrow">WELCOME TO YEP</span>
        <h2>{register ? "Make yourself at home." : "Welcome back."}</h2>
        <p>
          {register
            ? "Create an account to start your project."
            : "Sign in to your project workspace."}
        </p>
        <Form
          submit={register ? "Create account" : "Sign in"}
          onSubmit={async (f) => {
            const data = obj(f);
            if (register) await api("/auth/register", "POST", data);
            const u = await api("/auth/login", "POST", {
              email: data.email,
              password: data.password,
            });
            onDone(u);
          }}
        >
          {register && <Field label="Your name" name="name" />}
          <Field label="Email address" name="email" type="email" />
          <Field label="Password" name="password" type="password" />
          {register && (
            <p className="muted wide">
              Use 10 or more characters. Your account will have Customer access.
            </p>
          )}
        </Form>
        <p>
          {register ? "Already have an account?" : "New to YEP?"}{" "}
          <a href={register ? "#/login" : "#/register"}>
            {register ? "Sign in" : "Create an account"}
          </a>
        </p>
        <div className="demo">
          <strong>Explore the demo</strong>
          <p>
            All accounts use <code>Demo@12345</code>
          </p>
          <div className="demo-roles">
            {["customer", "owner", "manager", "worker"].map((r) => (
              <button
                key={r}
                onClick={async () => {
                  try {
                    onDone(
                      await api("/auth/login", "POST", {
                        email: r + "@yep.local",
                        password: "Demo@12345",
                      }),
                    );
                  } catch {
                    alert(
                      "Demo login unavailable. Run the backend seed script and confirm MongoDB is running.",
                    );
                  }
                }}
              >
                {r === "owner" ? "Admin" : r}
              </button>
            ))}
          </div>
        </div>
        <button className="link" onClick={() => go("/")}>
          Visit public website <ArrowUpRight size={14} />
        </button>
      </div>
    </div>
  );
}
