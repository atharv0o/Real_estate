/**
 * Compact trust indicator for on-chain attestations.
 */
export function BlockchainBadge() {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide text-emerald-300 backdrop-blur-sm">
      <span
        className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]"
        aria-hidden
      />
      Verified on Blockchain
    </span>
  );
}
