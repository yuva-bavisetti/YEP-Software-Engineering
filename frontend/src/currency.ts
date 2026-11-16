/** Exact half-up arithmetic for positive quantities (3dp), prices (2dp) and tax (2dp).
 * BigInt avoids binary floating-point surprises; the server independently validates totals.
 */
function scaled(value: string, places: number): bigint {
  const match = value.match(new RegExp(`^(\\d+)(?:\\.(\\d{0,${places}}))?$`));
  if (!match) return 0n;
  return (
    BigInt(match[1]) * 10n ** BigInt(places) +
    BigInt((match[2] || "").padEnd(places, "0"))
  );
}
export function lineCents(quantity: string, price: string): number {
  return Number((scaled(quantity, 3) * scaled(price, 2) + 500n) / 1000n);
}
export function grandTotal(
  subtotal: number,
  taxPercent: string,
  discount: string,
): number {
  if (!Number.isSafeInteger(subtotal) || subtotal < 0) return 0;
  const tax = (BigInt(subtotal) * scaled(taxPercent, 2) + 5000n) / 10000n;
  return Number(BigInt(subtotal) + tax - scaled(discount, 2));
}
