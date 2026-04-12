import { Suspense } from "react";

import { SearchPageFallback } from "@/components/Skeletons";

import SearchContent from "./SearchContent";

/**
 * Search results: requires Suspense because child uses useSearchParams().
 */
export default function SearchPage() {
  return (
    <Suspense fallback={<SearchPageFallback />}>
      <SearchContent />
    </Suspense>
  );
}
