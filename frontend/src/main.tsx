import { CheckCircle2 } from "lucide-react";
import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { api, Row } from "./api";
import Dashboard from "./features/Dashboard";
import Auth from "./pages/Auth";
import Public from "./pages/Public";
import "./style.css";
function App() {
  const [user, setUser] = useState<Row | null>(null);
  const [ready, setReady] = useState(false);
  const [path, setPath] = useState(location.hash.slice(1) || "/");
  const [toast, setToast] = useState("");
  useEffect(() => {
    api("/auth/me")
      .then(setUser)
      .catch(() => {})
      .finally(() => setReady(true));
    const h = () => setPath(location.hash.slice(1) || "/");
    addEventListener("hashchange", h);
    return () => removeEventListener("hashchange", h);
  }, []);
  const go = (p: string) => {
    location.hash = p;
  };
  const notify = (s: string) => {
    setToast(s);
    setTimeout(() => setToast(""), 5000);
  };
  if (!ready)
    return (
      <div className="loading">
        YEP <span>Preparing your workspace…</span>
      </div>
    );
  return (
    <>
      {toast && (
        <div className="toast" role="status">
          <CheckCircle2 size={18} />
          {toast}
        </div>
      )}
      {path.startsWith("/dashboard") ? (
        user ? (
          <Dashboard user={user} setUser={setUser} go={go} notify={notify} />
        ) : (
          <Auth
            register={false}
            onDone={(u) => {
              setUser(u);
              go("/dashboard");
            }}
            go={go}
          />
        )
      ) : path.startsWith("/login") || path === "/register" ? (
        <Auth
          register={path === "/register"}
          onDone={(u) => {
            setUser(u);
            go("/dashboard");
          }}
          go={go}
        />
      ) : (
        <Public path={path} go={go} user={user} notify={notify} />
      )}
    </>
  );
}
createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
