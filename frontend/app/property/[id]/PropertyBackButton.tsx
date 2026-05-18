"use client";

import { useRouter, useSearchParams } from "next/navigation";

export function PropertyBackButton() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const returnTo = searchParams.get("returnTo");

  const handleClick = () => {
    if (returnTo) {
      router.push(decodeURIComponent(returnTo), { scroll: false });
      return;
    }

    if (typeof window !== "undefined" && window.history.length > 1) {
      router.back();
      return;
    }

    router.push("/", { scroll: false });
  };

  return (
    <div className="mb-8">
      <button
        type="button"
        onClick={handleClick}
        className="inline-flex items-center text-sm font-medium text-sky-400 hover:text-sky-300"
      >
        ← Back to search
      </button>
    </div>
  );
}
