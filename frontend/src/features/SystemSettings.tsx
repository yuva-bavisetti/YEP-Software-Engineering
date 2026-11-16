import { useEffect, useState } from "react";
import { api, Row } from "../api";
import { Field, Form, Text } from "../components/ui";
export default function SystemSettings({
  notify,
}: {
  notify: (s: string) => void;
}) {
  const [data, setData] = useState<Row | null>(null),
    [error, setError] = useState("");
  useEffect(() => {
    api("/settings/public")
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);
  if (error) return <p className="error">{error}</p>;
  if (!data) return <p>Loading settings…</p>;
  return (
    <>
      <article className="card">
        <h2>Business contact settings</h2>
        <p>These fields appear on the public Contact page.</p>
        <Form
          submit="Save settings"
          onSubmit={async (f) => {
            await api("/admin/settings", "PUT", {
              business_name: f.get("business_name"),
              email: f.get("email") || null,
              phone: f.get("phone"),
              location: f.get("location"),
            });
            notify("Business settings updated");
          }}
        >
          <Field
            name="business_name"
            label="Business name"
            defaultValue={data.business_name}
          />
          <Field
            name="email"
            label="Contact email"
            type="email"
            required={false}
            defaultValue={data.email || ""}
          />
          <Field
            name="phone"
            label="Contact phone"
            required={false}
            defaultValue={data.phone}
          />
          <Text
            name="location"
            label="Location / service area"
            defaultValue={data.location}
          />
        </Form>
      </article>
      <article className="card table-wrap">
        <h2>Role permissions</h2>
        <p>
          Financial, inspection and chat boundaries follow the required business
          rules. Employee roles can be changed in Team after active duties are
          reassigned. Admin privileges are not assignable through public
          registration.
        </p>
        <table>
          <thead>
            <tr>
              <th>Role</th>
              <th>Requests / initial inspection</th>
              <th>Quotations / finances</th>
              <th>Project chats</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Customer</td>
              <td>Own requests / read status</td>
              <td>Own only / payments read-only</td>
              <td>Customer Chat only</td>
            </tr>
            <tr>
              <td>Admin</td>
              <td>All / conduct inspection</td>
              <td>Create, publish, verify offline payments</td>
              <td>Both</td>
            </tr>
            <tr>
              <td>Manager</td>
              <td>No initial requests or inspections</td>
              <td>No access</td>
              <td>Both, assigned projects only</td>
            </tr>
            <tr>
              <td>Worker</td>
              <td>No access</td>
              <td>No access</td>
              <td>Internal Chat, assigned projects only</td>
            </tr>
          </tbody>
        </table>
      </article>
    </>
  );
}
