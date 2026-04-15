type BlockchainBadgeProps = {
  verified?: boolean;
  hash?: string | null;
  className?: string;
};

/**
 * Trust indicator for record attestation (local hash + optional on-chain verify).
 */
export function BlockchainBadge({ verified = true, hash, className = "" }: BlockchainBadgeProps) {
  if (verified === false && !hash) {
    return null;
  }

  return (
    <span
      className={`inline-flex max-w-full flex-col items-start gap-0.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide text-emerald-300 backdrop-blur-sm ${className}`}
    >
      <span className="inline-flex items-center gap-1.5">
        <span
          className="inline-block h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]"
          aria-hidden
        />
        {verified ? "Verified" : "Pending"}
      </span>
      {hash ? (
        <span className="w-full truncate font-mono normal-case text-[9px] text-emerald-200/80" title={hash}>
          {hash.slice(0, 14)}…
        </span>
      ) : null}
    </span>
  );
}
