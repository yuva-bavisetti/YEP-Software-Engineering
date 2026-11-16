import { Plus } from "lucide-react";
import { useEffect, useState } from "react";
import { api, date, money, Row, short } from "../api";
import { Button, Field, Form, obj, Select, Text } from "../components/ui";

export default function Finance({
  project,
  admin,
  notify,
}: {
  project: Row;
  admin: boolean;
  notify: (s: string) => void;
}) {
  const [data, setData] = useState<Row | null>(null);
  const [open, setOpen] = useState(false);
  const [version, setVersion] = useState(0);
  const [key, setKey] = useState(crypto.randomUUID());
  useEffect(() => {
    api("/projects/" + project.id + "/finance")
      .then(setData)
      .catch((e) => notify(e.message));
  }, [project.id, version]);
  return (
    <article className="card">
      <div className="card-head">
        <div>
          <small>{short(project.id)}</small>
          <h2>{project.title}</h2>
        </div>
        {admin && (
          <Button secondary onClick={() => setOpen(!open)}>
            <Plus size={15} /> Record verified payment
          </Button>
        )}
      </div>
      {data && (
        <>
          <div className="finance-summary">
            <div>
              <small>Total payable</small>
              <strong>{money(data.total_cents)}</strong>
            </div>
            <div>
              <small>Amount paid</small>
              <strong>{money(data.paid_cents)}</strong>
            </div>
            <div>
              <small>Remaining balance</small>
              <strong>{money(data.balance_cents)}</strong>
            </div>
          </div>
          <div
            className="progress-track"
            role="progressbar"
            aria-label="Verified payments against payable"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={
              data.total_cents > 0
                ? Math.min(
                    100,
                    Math.max(
                      0,
                      Math.floor((data.paid_cents / data.total_cents) * 100),
                    ),
                  )
                : 0
            }
          >
            <div
              style={{
                width:
                  (data.total_cents > 0
                    ? Math.min(
                        100,
                        Math.max(0, (data.paid_cents / data.total_cents) * 100),
                      )
                    : 0) + "%",
              }}
            />
          </div>
          {data.balance_cents < 0 && (
            <p className="notice">
              Customer credit: {money(-data.balance_cents)}. The overpayment is
              preserved in the ledger.
            </p>
          )}
          <p className="muted tiny">
            Payable includes accepted Phase 1 and published or accepted
            subsequent phases. Payments are verified offline; quotations are not
            revenue.
          </p>
          {open && (
            <Form
              submit="Record offline-verified payment"
              onSubmit={async (f) => {
                await api("/projects/" + project.id + "/payments", "POST", {
                  ...obj(f),
                  idempotency_key: key,
                });
                setKey(crypto.randomUUID());
                setOpen(false);
                setVersion((v) => v + 1);
                notify("Verified payment recorded");
              }}
            >
              <Field
                label="Amount received (INR)"
                name="amount"
                type="number"
                min={0.01}
                step="0.01"
              />
              <Field label="Payment date" name="date" type="date" />
              <Select
                label="Method"
                name="method"
                options={["Cash", "UPI", "Bank Transfer", "Other"]}
              />
              <Field
                label="Transaction/reference number"
                name="reference"
                required={false}
              />
              <Text
                label="Offline verification information"
                name="verification"
              />
              <Text label="Notes" name="notes" required={false} />
            </Form>
          )}
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Method</th>
                  <th>Reference</th>
                  <th>Amount</th>
                  <th>Verification / correction</th>
                </tr>
              </thead>
              <tbody>
                {data.payments.map((p: Row) => (
                  <tr key={p.id}>
                    <td>{date(p.date)}</td>
                    <td>{p.method}</td>
                    <td>{p.reference || "—"}</td>
                    <td>{money(p.amount_cents)}</td>
                    <td>
                      {p.verification || p.notes}
                      {admin &&
                        p.amount_cents > 0 &&
                        !data.payments.some(
                          (x: Row) => x.reverses === p.id,
                        ) && (
                          <button
                            onClick={async () => {
                              const reason = prompt(
                                "Reason for reversal (audit history is preserved)",
                              );
                              if (!reason) return;
                              try {
                                await api(
                                  "/payments/" + p.id + "/reverse",
                                  "POST",
                                  { text: reason },
                                );
                                setVersion((v) => v + 1);
                              } catch (e) {
                                notify((e as Error).message);
                              }
                            }}
                          >
                            Reverse payment
                          </button>
                        )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {data.payments.length === 0 && (
              <p className="muted">No verified payments recorded yet.</p>
            )}
          </div>
        </>
      )}
    </article>
  );
}
