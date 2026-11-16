import { Plus, X } from "lucide-react";
import { useState } from "react";
import { api, money, Row, upload } from "../api";
import { Button, Field, Form, Text } from "../components/ui";
import { grandTotal, lineCents } from "../currency";
type Item = {
  description: string;
  category: string;
  quantity: string;
  unit: string;
  unit_price: string;
};
export default function QuoteBuilder({
  request,
  quote,
  onDone,
  close,
}: {
  request: Row;
  quote?: Row;
  onDone: () => void;
  close: () => void;
}) {
  const [items, setItems] = useState<Item[]>(
    quote?.items?.map((i: Row) => ({
      description: i.description,
      category: i.category,
      quantity: i.quantity,
      unit: i.unit,
      unit_price: String(i.unit_price_cents / 100),
    })) || [],
  );
  const [tax, setTax] = useState(quote?.tax_percent || "0");
  const [discount, setDiscount] = useState(
    String((quote?.discount_cents || 0) / 100),
  );
  const subtotal = items.reduce(
    (sum, i) => sum + lineCents(i.quantity, i.unit_price),
    0,
  );
  const total = grandTotal(subtotal, tax, discount);
  const update = (index: number, key: keyof Item, value: string) =>
    setItems(items.map((i, n) => (n === index ? { ...i, [key]: value } : i)));
  return (
    <Form
      close={close}
      submit="Save quotation draft"
      onSubmit={async (f) => {
        const file = f.get("pdf") as File;
        if (!file?.size && !quote) throw new Error("Attach the quotation PDF");
        const pdf = file?.size ? await upload(file) : { id: quote?.pdf_id };
        await api(
          quote ? "/quotes/" + quote.id : "/requests/" + request.id + "/quotes",
          quote ? "PUT" : "POST",
          {
            phase: Number(f.get("phase")),
            title: f.get("title"),
            description: f.get("description"),
            amount: items.length ? (total / 100).toFixed(2) : f.get("amount"),
            duration: Number(f.get("duration")),
            terms: f.get("terms"),
            pdf_id: pdf.id,
            items,
            tax_percent: items.length ? tax : "0",
            discount: items.length ? discount : "0",
          },
        );
        onDone();
      }}
    >
      <Field
        label="Phase number"
        name="phase"
        type="number"
        min={1}
        defaultValue={quote?.phase || 1}
      />
      <Field label="Phase title" name="title" defaultValue={quote?.title} />
      <Field
        label="Duration (days)"
        name="duration"
        type="number"
        min={1}
        defaultValue={quote?.duration}
      />
      {items.length ? (
        <label>
          Calculated quotation total
          <input
            value={(total / 100).toFixed(2)}
            readOnly
            aria-label="Calculated quotation total"
          />
        </label>
      ) : (
        <Field
          label="Total amount (INR)"
          name="amount"
          type="number"
          min={0.01}
          step="0.01"
          defaultValue={quote ? quote.amount_cents / 100 : undefined}
        />
      )}
      <Text
        label="Description of work"
        name="description"
        defaultValue={quote?.description}
      />
      <div className="wide boq">
        <div className="card-head">
          <h3>
            Bill of quantities <small>Optional</small>
          </h3>
          <Button
            secondary
            onClick={() =>
              setItems([
                ...items,
                {
                  description: "",
                  category: "Material",
                  quantity: "1",
                  unit: "sq ft",
                  unit_price: "0",
                },
              ])
            }
          >
            <Plus size={14} />
            Add line item
          </Button>
        </div>
        {items.map((i, n) => (
          <div className="boq-item" key={n}>
            <label>
              Item description
              <input
                required
                value={i.description}
                onChange={(e) => update(n, "description", e.target.value)}
              />
            </label>
            <label>
              Category
              <select
                value={i.category}
                onChange={(e) => update(n, "category", e.target.value)}
              >
                {["Material", "Labour", "Other"].map((c) => (
                  <option key={c}>{c}</option>
                ))}
              </select>
            </label>
            <label>
              Quantity
              <input
                type="number"
                required
                min="0.001"
                step="0.001"
                value={i.quantity}
                onChange={(e) => update(n, "quantity", e.target.value)}
              />
            </label>
            <label>
              Unit
              <input
                required
                value={i.unit}
                onChange={(e) => update(n, "unit", e.target.value)}
              />
            </label>
            <label>
              Unit price (INR)
              <input
                type="number"
                min="0"
                step="0.01"
                required
                value={i.unit_price}
                onChange={(e) => update(n, "unit_price", e.target.value)}
              />
            </label>
            <span>{money(lineCents(i.quantity, i.unit_price))}</span>
            <button
              type="button"
              aria-label="Remove line item"
              onClick={() => setItems(items.filter((_, index) => index !== n))}
            >
              <X size={15} />
            </button>
          </div>
        ))}
        {items.length > 0 && (
          <div className="form-grid">
            <label>
              Tax (%)
              <input
                type="number"
                min="0"
                max="100"
                step="0.01"
                value={tax}
                onChange={(e) => setTax(e.target.value)}
              />
            </label>
            <label>
              Discount (INR)
              <input
                type="number"
                min="0"
                step="0.01"
                value={discount}
                onChange={(e) => setDiscount(e.target.value)}
              />
            </label>
            <p>
              Subtotal: {money(subtotal)} · Grand total: {money(total)}
            </p>
          </div>
        )}
      </div>
      <Text
        label="Terms and conditions"
        name="terms"
        defaultValue={quote?.terms}
      />
      <label className="wide">
        Quotation PDF · multi-page · up to 10 MB
        <input
          name="pdf"
          type="file"
          accept="application/pdf"
          required={!quote}
        />
      </label>
      <p className="wide muted">
        The PDF should match this quotation. The server validates BOQ
        calculations; it does not extract totals from uploaded PDFs.
      </p>
    </Form>
  );
}
