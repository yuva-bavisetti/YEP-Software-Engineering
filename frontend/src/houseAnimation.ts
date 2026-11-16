/** Hold an unfinished shell, finish it over six seconds, then hold the result. */
export function finishProgress(seconds: number, reducedMotion = false): number {
  if (reducedMotion) return 1;
  const cycle = Math.max(0, seconds) % 18;
  const x = Math.min(1, Math.max(0, (cycle - 2) / 6));
  return x * x * (3 - 2 * x);
}
