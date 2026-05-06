import { notFound } from "next/navigation";

import { ChatBox } from "@/components/ChatBox";
import { PropertyBackButton } from "./PropertyBackButton";
import { PropertyDetailLiveClient } from "./PropertyDetailLiveClient";

type PageProps = { params: Promise<{ id: string }> };

/**
 * Property detail — hydrates from Zustand on the client when available,
 * otherwise shows a deterministic mock for direct URL visits.
 */
export default async function PropertyDetailPage({ params }: PageProps) {
  const { id } = await params;
  if (!id) notFound();

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 md:py-14">
      <PropertyBackButton />

      <div className="grid gap-10 lg:grid-cols-[1fr_360px]">
        <div>
          <PropertyDetailLiveClient id={id} />
        </div>
        <div className="lg:sticky lg:top-24 lg:self-start">
          <ChatBox />
        </div>
      </div>
    </div>
  );
}
