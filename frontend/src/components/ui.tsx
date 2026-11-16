import { ArrowRight, FolderKanban } from "lucide-react";
import React, { useState } from "react";

export function Button({
  children,
  onClick,
  secondary = false,
  disabled = false,
  type = "button",
}: {
  children: React.ReactNode;
  onClick?: () => void;
  secondary?: boolean;
  disabled?: boolean;
  type?: "button" | "submit";
}) {
  return (
    <button
      type={type}
      disabled={disabled}
      className={secondary ? "btn secondary" : "btn"}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

export function Badge({ children }: { children: React.ReactNode }) {
  return <span className="badge">{children}</span>;
}

export function Field({
  label,
  name,
  type = "text",
  required = true,
  defaultValue,
  min,
  max,
  step,
  placeholder,
}: {
  label: string;
  name: string;
  type?: string;
  required?: boolean;
  defaultValue?: string | number;
  min?: number;
  max?: number;
  step?: string;
  placeholder?: string;
}) {
  return (
    <label>
      {label}
      <input
        name={name}
        type={type}
        required={required}
        defaultValue={defaultValue}
        min={min}
        max={max}
        step={step}
        placeholder={placeholder}
      />
    </label>
  );
}

export function Select({
  label,
  name,
  options,
  defaultValue,
}: {
  label: string;
  name: string;
  options: (string | { value: string; label: string })[];
  defaultValue?: string | number;
}) {
  return (
    <label>
      {label}
      <select name={name} required defaultValue={defaultValue}>
        {options.map((v) =>
          typeof v === "string" ? (
            <option key={v}>{v}</option>
          ) : (
            <option key={v.value} value={v.value}>
              {v.label}
            </option>
          ),
        )}
      </select>
    </label>
  );
}

export function Text({
  label,
  name,
  required = true,
  defaultValue,
}: {
  label: string;
  name: string;
  required?: boolean;
  defaultValue?: string;
}) {
  return (
    <label className="wide">
      {label}
      <textarea
        name={name}
        required={required}
        rows={3}
        defaultValue={defaultValue}
      />
    </label>
  );
}

export function Form({
  children,
  onSubmit,
  submit = "Save",
  close,
}: {
  children: React.ReactNode;
  onSubmit: (f: FormData) => Promise<void>;
  submit?: string;
  close?: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  return (
    <form
      onSubmit={async (e) => {
        e.preventDefault();
        setBusy(true);
        setError("");
        try {
          const data = new FormData(e.currentTarget);
          const fileInputs = Array.from(
            e.currentTarget.querySelectorAll<HTMLInputElement>(
              'input[type="file"][name]',
            ),
          ).filter((input) => !input.disabled);
          for (const name of new Set(fileInputs.map((input) => input.name)))
            data.delete(name);
          for (const input of fileInputs)
            for (const file of Array.from(input.files || []))
              data.append(input.name, file);
          await onSubmit(data);
        } catch (e) {
          setError((e as Error).message);
        } finally {
          setBusy(false);
        }
      }}
    >
      <div className="form-grid">{children}</div>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      <div className="actions">
        <Button type="submit" disabled={busy}>
          {busy ? "Saving…" : submit}
          <ArrowRight size={16} />
        </Button>
        {close && (
          <Button secondary onClick={close}>
            Cancel
          </Button>
        )}
      </div>
    </form>
  );
}

export function Empty({ title, text }: { title: string; text: string }) {
  return (
    <div className="empty">
      <FolderKanban size={28} />
      <h3>{title}</h3>
      <p>{text}</p>
    </div>
  );
}
export const obj = (f: FormData) =>
  Object.fromEntries([...f.entries()].filter(([, v]) => typeof v === "string"));
