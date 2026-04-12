import Link from "next/link";
import { notFound } from "next/navigation";

import { ChatBox } from "@/components/ChatBox";
import { getMockPropertyData } from "@/lib/api";
import { PropertyDetailClient } from "./PropertyDetailClient";

type PageProps = { params: Promise<{ id: string }> };

/**
 * Property detail — hydrates from Zustand on the client when available,
 * otherwise shows a deterministic mock for direct URL visits.
 */
export default async function PropertyDetailPage({ params }: PageProps) {
  const { id } = await params;
  if (!id) notFound();

  const fallback = getMockPropertyData({
    district: "",
    city: "",
    area: id.replace(/^mock-/, "").replace(/-/g, " "),
    pinCode: "110001",
    landAreaCode: "DEMO"
  });

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 md:py-14">
      <Link
        href="/search"
        className="mb-8 inline-block text-sm font-medium text-sky-400 hover:text-sky-300"
      >
        ← Back to search
      </Link>

      <div className="grid gap-10 lg:grid-cols-[1fr_360px]">
        <div>
          <PropertyDetailClient id={id} fallback={fallback} />
        </div>
        <div className="lg:sticky lg:top-24 lg:self-start">
          <ChatBox />
        </div>
      </div>
    </div>
  );
}
