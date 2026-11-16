import { describe, expect, it } from "vitest";
import { grandTotal, lineCents } from "../currency";
describe("BOQ money arithmetic", () => {
  it("rounds fractional paise half up without binary floating-point drift", () => {
    expect(lineCents("0.1", "0.05")).toBe(1);
    expect(lineCents("2.5", "99.00")).toBe(24750);
    expect(lineCents("1.005", "10.00")).toBe(1005);
  });
  it("applies tax and discount to the subtotal in integer paise", () => {
    expect(grandTotal(24750, "10", "21.50")).toBe(25075);
    expect(grandTotal(1, "50", "0")).toBe(2);
  });
});
