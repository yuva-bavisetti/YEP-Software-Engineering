import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { api, upload } from "../api";
import { serviceNames } from "../constants";
import Dashboard from "../features/Dashboard";
import Finance from "../features/Finance";
import QuoteBuilder from "../features/QuoteBuilder";
import Public from "../pages/Public";
vi.mock("../api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api")>();
  return { ...actual, api: vi.fn(), upload: vi.fn() };
});
vi.mock("../components/HouseScene", () => ({
  default: () => <div aria-label="House scene test substitute" />,
}));
const project = {
  id: "project-001",
  request_id: "request-001",
  title: "The Morgan residence",
  location: "Pune",
  progress: 58,
  status: "Active",
  start_date: "2026-11-20",
  deadline: "2026-12-20",
  phases: [{ number: 1, title: "Preparation", duration: 14, status: "Active" }],
  worker_ids: ["worker-1"],
  manager_id: "manager-1",
  manager_name: "Rohan Shah",
  team: [{ id: "worker-1", name: "Dev Patel" }],
};
const request = {
  id: "request-001",
  service: "Interior painting",
  status: "Submitted",
  created_at: "2026-11-16",
  description: "Paint the living room and bedrooms",
  location: "Pune",
  area: 1200,
  rooms: 3,
  file_ids: [],
};
const notify = vi.fn();
beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api).mockImplementation(async (path, method = "GET", body) => {
    if (path === "/services") return serviceNames.map((name) => ({ name }));
    if (path === "/projects") return [project];
    if (path === "/requests")
      return method === "GET"
        ? [request]
        : { id: "new-request", ...(body as object) };
    if (path === "/quotes") return [];
    if (path === "/users")
      return [
        { id: "manager-1", role: "MANAGER", name: "Rohan Shah", active: true },
      ];
    if (path.includes("/inspection")) return null;
    return [];
  });
  vi.mocked(upload).mockResolvedValue({ id: "file-uploaded" });
});
function dashboard(role: string) {
  return render(
    <Dashboard
      user={{
        id: role.toLowerCase() + "-1",
        name: "Alex Morgan",
        email: role.toLowerCase() + "@yep.local",
        role,
      }}
      setUser={vi.fn()}
      go={vi.fn()}
      notify={notify}
    />,
  );
}
describe("Role workspaces", () => {
  it.each(["ADMIN", "CUSTOMER", "MANAGER", "WORKER"])(
    "renders the %s dashboard with the right navigation",
    async (role) => {
      dashboard(role);
      await screen.findByRole("heading", { name: "Hello, Alex." });
      expect(screen.getByText("The Morgan residence")).toBeTruthy();
      if (["MANAGER", "WORKER"].includes(role)) {
        expect(
          screen.queryByRole("button", { name: "Quotations & Payments" }),
        ).toBeNull();
        expect(
          screen.queryByRole("button", { name: "Requests" }),
        ).toBeNull();
        expect(
          vi
            .mocked(api)
            .mock.calls.some(([p]) => p === "/quotes" || p === "/requests"),
        ).toBe(false);
      }
      if (role === "CUSTOMER")
        expect(
          screen.getByRole("button", { name: "AI Design Studio" }),
        ).toBeTruthy();
      if (role === "ADMIN")
        expect(
          screen.getByRole("button", { name: "Team" }),
        ).toBeTruthy();
    },
  );
  it("submits customer request details to Admin without file-form fields", async () => {
    dashboard("CUSTOMER");
    await screen.findByRole("heading", { name: "Hello, Alex." });
    await userEvent.click(
      screen.getByRole("button", { name: "New Request" }),
    );
    await userEvent.type(
      screen.getByLabelText("Property location"),
      "Baner, Pune",
    );
    await userEvent.type(screen.getByLabelText("Area (sq ft)"), "1200");
    await userEvent.type(
      screen.getByLabelText("Describe your project (at least 10 characters)"),
      "Refresh the living room and bedrooms",
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Submit project request" }),
    );
    await waitFor(() =>
      expect(api).toHaveBeenCalledWith(
        "/requests",
        "POST",
        expect.objectContaining({
          area: 1200,
          rooms: 1,
          location: "Baner, Pune",
          file_ids: [],
        }),
      ),
    );
    const body = vi
      .mocked(api)
      .mock.calls.find(
        ([p, m]) => p === "/requests" && m === "POST",
      )?.[2] as object;
    expect(body).not.toHaveProperty("photos");
    expect(notify).toHaveBeenCalledWith("Request submitted to Admin");
  });
  it("keeps the five AI interfaces available without fabricated responses", async () => {
    dashboard("CUSTOMER");
    await screen.findByRole("heading", { name: "Hello, Alex." });
    for (const tab of [
      "AI Design Studio",
      "AI Assistant",
      "AI Cost Estimator",
      "Smart Recommendations",
      "AI Project Insights",
    ]) {
      await userEvent.click(
        screen.getByRole("button", { name: tab }),
      );
      expect(screen.getByText(/No AI model is connected/)).toBeTruthy();
      expect(screen.queryByText(/coming soon/i)).toBeNull();
    }
    expect(vi.mocked(api).mock.calls.every(([p]) => !p.includes("/ai"))).toBe(
      true,
    );
  });
  it("sends a strict inspection payload without the file input name", async () => {
    dashboard("ADMIN");
    await screen.findByRole("heading", { name: "Hello, Alex." });
    await userEvent.click(
      screen.getByRole("button", { name: "Requests" }),
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Record inspection" }),
    );
    fireEvent.change(screen.getByLabelText("Inspection date"), {
      target: { value: "2026-11-16" },
    });
    await userEvent.selectOptions(screen.getByLabelText("Status"), "true");
    await userEvent.type(
      screen.getByLabelText("Site measurements"),
      "1200 sq ft",
    );
    await userEvent.type(
      screen.getByLabelText("Inspection findings"),
      "Walls require primer",
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Save inspection" }),
    );
    await waitFor(() =>
      expect(api).toHaveBeenCalledWith(
        "/requests/request-001/inspection",
        "POST",
        {
          date: "2026-11-16",
          measurements: "1200 sq ft",
          notes: "Walls require primer",
          materials: "",
          completed: true,
          file_ids: [],
        },
      ),
    );
  });
});
describe("Public website and finance", () => {
  it.each([
    ["/", "Good spaces."],
    ["/services", "Services for every space."],
    ["/projects", "Spaces with a new story."],
    ["/about", "Built on care."],
    ["/how-it-works", "From first idea to final detail."],
    ["/contact", "We’re listening."],
  ])("renders public page %s", async (path, heading) => {
    render(<Public path={path} go={vi.fn()} user={null} notify={notify} />);
    expect(
      screen.getAllByRole("heading", { level: 1 })[0].textContent,
    ).toContain(heading);
    expect(screen.getByRole("navigation")).toBeTruthy();
    if (path === "/")
      expect(
        screen.getAllByRole("button", { name: "Start New Project" }),
      ).toHaveLength(1);
  });
  it("renders server-provided payable, paid and balance totals", async () => {
    vi.mocked(api).mockResolvedValue({
      total_cents: 13000000,
      paid_cents: 3000000,
      balance_cents: 10000000,
      payments: [],
    });
    render(<Finance project={project} admin={false} notify={notify} />);
    await screen.findByText("Total payable");
    expect(screen.getByText("₹1,30,000.00")).toBeTruthy();
    expect(screen.getByText("₹30,000.00")).toBeTruthy();
    expect(screen.getByText("₹1,00,000.00")).toBeTruthy();
    expect(
      screen.queryByRole("button", { name: /Record verified payment/ }),
    ).toBeNull();
  });
  it("edits a draft while retaining the existing protected PDF", async () => {
    const q = {
      id: "quote-001",
      phase: 1,
      title: "Paint draft",
      description: "Prepare and paint living room",
      duration: 14,
      amount_cents: 250000,
      pdf_id: "pdf-existing",
      terms: "Offline payments only",
      items: [],
    };
    render(
      <QuoteBuilder
        request={{ id: "request-001" }}
        quote={q}
        onDone={notify}
        close={vi.fn()}
      />,
    );
    await userEvent.clear(screen.getByLabelText("Phase title"));
    await userEvent.type(screen.getByLabelText("Phase title"), "Updated phase");
    await userEvent.click(
      screen.getByRole("button", { name: "Save quotation draft" }),
    );
    await waitFor(() =>
      expect(api).toHaveBeenCalledWith(
        "/quotes/quote-001",
        "PUT",
        expect.objectContaining({
          title: "Updated phase",
          pdf_id: "pdf-existing",
          duration: 14,
        }),
      ),
    );
    expect(upload).not.toHaveBeenCalled();
  });
});
