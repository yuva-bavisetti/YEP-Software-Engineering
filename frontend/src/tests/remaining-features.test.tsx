import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, it, expect, vi } from "vitest";
import { api, upload } from "../api";
import PublicGallery from "../features/PublicGallery";
import ServiceCatalogue from "../features/ServiceCatalogue";
import ExecutionReports from "../features/ExecutionReports";
import ExecutionPanel from "../features/ExecutionPanel";
import PortfolioSettings from "../features/PortfolioSettings";
import Project from "../features/Project";
import WorkspaceInsights from "../features/WorkspaceInsights";
import AdminPanel from "../features/AdminPanel";
import Dashboard from "../features/Dashboard";
import Public from "../pages/Public";
import SystemSettings from "../features/SystemSettings";
vi.mock("../api", async (original) => {
  const actual = await original<typeof import("../api")>();
  return { ...actual, api: vi.fn(), upload: vi.fn() };
});
vi.mock("../components/HouseScene", () => ({
  default: () => <div>House scene test substitute</div>,
}));
const p = {
  id: "p1",
  request_id: "r1",
  title: "A considered renovation",
  location: "Pune",
  progress: 50,
  status: "Active",
  start_date: "2026-11-16",
  deadline: "2026-12-01",
  manager_id: "manager",
  manager_name: "Manager A",
  worker_ids: ["worker"],
  team: [{ id: "worker", name: "Worker A" }],
  phases: [
    {
      number: 1,
      title: "Preparation",
      duration: 14,
      status: "Active",
      start_date: "2026-11-16",
      deadline: "2026-12-01",
    },
    {
      number: 2,
      title: "Finishing",
      duration: 7,
      status: "Planned",
      start_date: "",
      deadline: "",
    },
  ],
};
const user = {
  id: "manager",
  role: "MANAGER",
  name: "Manager A",
  email: "manager@yep.local",
};
const notify = vi.fn();
beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(upload).mockResolvedValue({ id: "image-upload" });
  vi.mocked(api).mockImplementation(async (path, method = "GET") => {
    if (path === "/services")
      return [
        {
          id: "s1",
          name: "Interior painting",
          description: "Carefully prepared finishes",
          image_id: "i1",
        },
      ];
    if (path === "/projects") return [p];
    if (path === "/users")
      return [
        { id: "worker", name: "Worker A", role: "WORKER", active: true },
        { id: "manager", name: "Manager A", role: "MANAGER", active: true },
      ];
    if (path === "/settings/public")
      return {
        business_name: "YEP",
        email: "contact@yep.local",
        phone: "12345",
        location: "Pune service area",
      };
    if (path === "/projects/p1/portfolio") return null;
    return [];
  });
});
describe("Public data-backed features", () => {
  it("filters completed database projects by category and displays approved feedback", async () => {
    vi.mocked(api).mockResolvedValue([
      {
        id: "a",
        project_id: "p1",
        title: "Restored floor",
        description: "Natural finish",
        category: "Flooring",
        file_ids: ["f1"],
        feedback: { rating: 5, text: "Carefully finished" },
      },
      {
        id: "b",
        project_id: "p2",
        title: "Fresh walls",
        description: "Warm palette",
        category: "Painting",
        file_ids: ["f2"],
      },
    ]);
    render(<PublicGallery />);
    await screen.findByText("Restored floor");
    await userEvent.click(screen.getByRole("button", { name: "Flooring" }));
    expect(screen.queryByText("Fresh walls")).toBeNull();
    expect(screen.getByAltText("Restored floor").getAttribute("src")).toBe(
      "/api/public/projects/p1/photos/f1",
    );
  });
  it("uses stable service IDs, saved descriptions and managed image URLs", async () => {
    render(<ServiceCatalogue path="/services/s1" />);
    await screen.findByText("Carefully prepared finishes");
    expect(
      screen.getByRole("heading", { name: "Interior painting", level: 1 }),
    ).toBeTruthy();
    expect(screen.getByRole("img").getAttribute("src")).toBe(
      "/api/public/services/s1/image",
    );
  });
  it("submits an enquiry and shows saved contact details", async () => {
    render(<Public path="/contact" go={vi.fn()} user={null} notify={notify} />);
    await screen.findByText("contact@yep.local");
    await userEvent.type(screen.getByLabelText("Your name"), "Sam Visitor");
    await userEvent.type(screen.getByLabelText("Email"), "sam@example.com");
    await userEvent.type(
      screen.getByLabelText("How can we help?"),
      "I would like to discuss a renovation",
    );
    await userEvent.click(screen.getByRole("button", { name: "Send enquiry" }));
    await waitFor(() =>
      expect(api).toHaveBeenCalledWith(
        "/enquiries",
        "POST",
        expect.objectContaining({
          name: "Sam Visitor",
          email: "sam@example.com",
          message: "I would like to discuss a renovation",
        }),
      ),
    );
  });
  it("preserves the project-request destination through the registration handoff", async () => {
    const go = vi.fn();
    const view = render(
      <Public path="/" go={go} user={null} notify={notify} />,
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Start New Project" }),
    );
    expect(go).toHaveBeenCalledWith("/register");
    expect(sessionStorage.getItem("newRequest")).toBe("yes");
    view.unmount();
    render(
      <Dashboard
        user={{ ...user, role: "CUSTOMER" }}
        setUser={vi.fn()}
        go={vi.fn()}
        notify={notify}
      />,
    );
    await screen.findByRole("heading", { name: "New Request" });
    expect(
      screen.getByRole("button", { name: "Submit project request" }),
    ).toBeTruthy();
  });
});
describe("Execution and administration", () => {
  it("renders scoped manager reports without fetching financial APIs", async () => {
    vi.mocked(api).mockResolvedValue({
      projects: [{ ...p, current_phase: "Preparation", workers: 1 }],
      task_status: { Pending: 2, Completed: 1 },
      pending_evidence: 1,
      shortages: [],
      issues: [],
    });
    render(<ExecutionReports />);
    await screen.findByText("A considered renovation");
    expect(screen.getByText("Pending: 2")).toBeTruthy();
    expect(api).toHaveBeenCalledTimes(1);
    expect(api).toHaveBeenCalledWith("/reports");
  });
  it("shows current phase, due work and actual manager instructions for workers", async () => {
    vi.mocked(api).mockResolvedValue({
      stats: {
        unread_notifications: 1,
        today_tasks: 1,
        pending_tasks: 2,
        completed_tasks: 3,
      },
      current_phases: [
        { project_id: "p1", project_title: p.title, phase: p.phases[0] },
      ],
      due_tasks: [
        {
          id: "t1",
          title: "Prime the wall",
          status: "Pending",
          deadline: "2026-11-16",
          description: "Protect the floor first",
        },
      ],
      instructions: [
        {
          id: "m1",
          text: "Use the low-VOC primer",
          sender_name: "Manager A",
          created_at: "2026-11-16",
        },
      ],
    });
    render(<WorkspaceInsights role="WORKER" />);
    await screen.findByText(/Use the low-VOC primer/);
    expect(screen.getByText(/Current phase 1/)).toBeTruthy();
    expect(screen.getByText(/Protect the floor first/)).toBeTruthy();
  });
  it("retains active phase status in schedule forms and adds planned phases", async () => {
    render(
      <Project
        project={p}
        user={{ ...user, role: "ADMIN" }}
        people={[
          { id: "worker", role: "WORKER", name: "Worker A", active: true },
        ]}
        notify={notify}
        refreshParent={vi.fn()}
        back={vi.fn()}
      />,
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Phases & Team" }),
    );
    expect(
      (screen.getAllByLabelText("Status")[0] as HTMLSelectElement).value,
    ).toBe("Active");
    await userEvent.click(screen.getByText("Plan another phase"));
    await userEvent.type(
      screen.getByLabelText("Phase name"),
      "Quality handover",
    );
    await userEvent.type(
      screen.getByLabelText("Estimated duration (days)"),
      "3",
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Add planned phase" }),
    );
    await waitFor(() =>
      expect(api).toHaveBeenCalledWith(
        "/projects/p1/phases",
        "POST",
        expect.objectContaining({
          number: 3,
          title: "Quality handover",
          duration: 3,
        }),
      ),
    );
  });
  it("creates a task for the selected phase with a numeric phase ID", async () => {
    render(
      <Project
        project={p}
        user={user}
        people={[{ id: "worker", role: "WORKER", name: "Worker A" }]}
        notify={notify}
        refreshParent={vi.fn()}
        back={vi.fn()}
      />,
    );
    await userEvent.click(screen.getByRole("button", { name: "Tasks" }));
    await userEvent.click(screen.getByRole("button", { name: "Create task" }));
    await userEvent.type(screen.getByLabelText("Task title"), "Final coat");
    await userEvent.selectOptions(screen.getByLabelText("Task phase"), "2");
    await userEvent.type(screen.getByLabelText("Deadline"), "2026-12-01");
    await userEvent.click(
      screen.getAllByRole("button", { name: "Create task" })[1],
    );
    await waitFor(() =>
      expect(api).toHaveBeenCalledWith(
        "/projects/p1/tasks",
        "POST",
        expect.objectContaining({ phase: 2, worker_id: "worker" }),
      ),
    );
  });
  it("submits a structured quality checklist instead of only a passed label", async () => {
    render(
      <ExecutionPanel project={p} user={user} tab="Quality" notify={notify} />,
    );
    await userEvent.type(
      screen.getByLabelText("Inspection checklist / area reviewed"),
      "Final room inspection",
    );
    await userEvent.selectOptions(screen.getByLabelText("Result"), "true");
    for (const label of [
      "Surface preparation",
      "Finish consistency",
      "Site clean-up",
    ])
      await userEvent.click(screen.getByLabelText(label));
    await userEvent.click(screen.getByRole("button", { name: "Save record" }));
    await waitFor(() =>
      expect(api).toHaveBeenCalledWith(
        "/projects/p1/quality",
        "POST",
        expect.objectContaining({
          passed: true,
          items: expect.arrayContaining([
            { label: "Finish consistency", passed: true },
          ]),
        }),
      ),
    );
  });
  it("publishes only selected approved photographs in the portfolio form", async () => {
    vi.mocked(api).mockImplementation(async (path) =>
      path.endsWith("/portfolio")
        ? null
        : [
            {
              id: "m1",
              file_id: "verified",
              verification: "Approved",
              text: "Verified work",
            },
            {
              id: "m2",
              file_id: "pending",
              verification: "Pending",
              text: "Pending work",
            },
          ],
    );
    render(
      <PortfolioSettings
        project={{ ...p, status: "Completed" }}
        notify={notify}
      />,
    );
    await screen.findByText("Verified work");
    expect(screen.queryByText("Pending work")).toBeNull();
    await userEvent.click(screen.getByRole("checkbox"));
    await userEvent.type(
      screen.getByLabelText("Public description"),
      "A careful, warm and natural renovation",
    );
    await userEvent.selectOptions(screen.getByLabelText("Publication"), "true");
    await userEvent.click(
      screen.getByRole("button", { name: "Save public portfolio" }),
    );
    await waitFor(() =>
      expect(api).toHaveBeenCalledWith(
        "/projects/p1/portfolio",
        "PUT",
        expect.objectContaining({ file_ids: ["verified"], published: true }),
      ),
    );
  });
  it("saves business contact settings to the Admin-only endpoint", async () => {
    render(<SystemSettings notify={notify} />);
    await screen.findByLabelText("Business name");
    await userEvent.clear(screen.getByLabelText("Contact phone"));
    await userEvent.type(screen.getByLabelText("Contact phone"), "98765");
    await userEvent.click(
      screen.getByRole("button", { name: "Save settings" }),
    );
    await waitFor(() =>
      expect(api).toHaveBeenCalledWith(
        "/admin/settings",
        "PUT",
        expect.objectContaining({ phone: "98765", email: "contact@yep.local" }),
      ),
    );
  });
  it("uploads and links a service image through the existing service editor", async () => {
    vi.mocked(api).mockImplementation(async (path) =>
      path === "/admin/services" ? [] : [],
    );
    render(<AdminPanel tab="Services" notify={notify} />);
    await userEvent.type(
      screen.getByLabelText("Service name"),
      "Wood finishing",
    );
    await userEvent.type(
      screen.getByLabelText("Description"),
      "Thoughtful preparation and a durable natural finish",
    );
    await userEvent.upload(
      screen.getByLabelText("Service photograph"),
      new File(["image-data"], "room.png", { type: "image/png" }),
    );
    await userEvent.click(screen.getByRole("button", { name: "Add service" }));
    await waitFor(() =>
      expect(api).toHaveBeenCalledWith(
        "/services",
        "POST",
        expect.objectContaining({
          name: "Wood finishing",
          image_id: "image-upload",
        }),
      ),
    );
  });
  it("shows actionable report errors without removing navigation", async () => {
    vi.mocked(api).mockRejectedValue(
      new Error("MongoDB is unavailable. Start the local service."),
    );
    render(<ExecutionReports />);
    expect(await screen.findByText(/MongoDB is unavailable/)).toBeTruthy();
  });
});

it("toggles public mobile navigation and closes it when a route is selected", async () => {
  render(<Public path="/" go={vi.fn()} user={null} notify={notify} />);
  const toggle = screen.getByRole("button", { name: "Toggle navigation" });
  await userEvent.click(toggle);
  expect(toggle.getAttribute("aria-expanded")).toBe("true");
  expect(screen.getByRole("navigation").classList.contains("open")).toBe(true);
  await userEvent.click(screen.getByRole("link", { name: "Services" }));
  expect(toggle.getAttribute("aria-expanded")).toBe("false");
});

it("marks only the selected notification read through its protected endpoint", async () => {
  vi.mocked(api).mockImplementation(async (path) => {
    if (path === "/projects") return [p];
    if (path === "/notifications")
      return [
        {
          id: "n1",
          text: "A project update is ready",
          created_at: "2026-11-16",
          read: false,
        },
      ];
    if (path === "/services") return [{ name: "Interior painting" }];
    return [];
  });
  render(
    <Dashboard
      user={{ ...user, role: "CUSTOMER" }}
      setUser={vi.fn()}
      go={vi.fn()}
      notify={notify}
    />,
  );
  await screen.findByRole("heading", { name: "Hello, Manager." });
  await userEvent.click(screen.getByRole("button", { name: "Mark as read" }));
  await waitFor(() =>
    expect(api).toHaveBeenCalledWith(
      "/notifications/n1/read",
      "PATCH",
      undefined,
    ),
  );
});
