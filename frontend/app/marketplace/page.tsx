"use client";

import { useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { BadgeCheck, MapPin, SlidersHorizontal, TrendingUp } from "lucide-react";

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger
} from "@/components/ui/accordion";
import { Card, CardContent } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { fetchRecommendations, getApiErrorMessage } from "@/lib/api";
import { cn } from "@/lib/utils";

type Property = {
  id: string;
  title: string;
  price: number;
  location: string;
  roi: number;
  trustScore: number;
  isVerified: boolean;
};

type SortOption = "price" | "roi" | "trustScore";

const properties: Property[] = [
  {
    id: "p-01",
    title: "Skyline Residences",
    price: 720000,
    location: "Mumbai",
    roi: 8.4,
    trustScore: 94,
    isVerified: true
  },
  {
    id: "p-02",
    title: "Palm Court Villas",
    price: 1180000,
    location: "Goa",
    roi: 7.8,
    trustScore: 88,
    isVerified: true
  },
  {
    id: "p-03",
    title: "Central Park Loft",
    price: 540000,
    location: "Bengaluru",
    roi: 9.2,
    trustScore: 82,
    isVerified: false
  },
  {
    id: "p-04",
    title: "Riverfront Estate",
    price: 960000,
    location: "Pune",
    roi: 6.9,
    trustScore: 91,
    isVerified: true
  },
  {
    id: "p-05",
    title: "Garden Square Homes",
    price: 430000,
    location: "Hyderabad",
    roi: 8.9,
    trustScore: 76,
    isVerified: false
  },
  {
    id: "p-06",
    title: "Marina Bay Suites",
    price: 1320000,
    location: "Mumbai",
    roi: 7.4,
    trustScore: 97,
    isVerified: true
  }
];

const locations = Array.from(new Set(properties.map((property) => property.location)));
const formatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0
});

function PropertyCard({ property }: { property: Property }) {
  return (
    <Card className="overflow-hidden border-border/70 bg-card/95 shadow-none transition-colors hover:border-primary/30">
      <CardContent className="space-y-5 p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-2">
            <h2 className="text-lg font-semibold tracking-normal">{property.title}</h2>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <MapPin className="h-4 w-4" />
              <span>{property.location}</span>
            </div>
          </div>
          {property.isVerified && (
            <span className="inline-flex items-center gap-1 rounded-full border border-accent/20 bg-accent/10 px-3 py-1 text-xs font-medium text-accent">
              <BadgeCheck className="h-3.5 w-3.5" />
              Verified
            </span>
          )}
        </div>

        <div className="grid grid-cols-3 gap-3 text-sm">
          <div>
            <p className="text-xs text-muted-foreground">Price</p>
            <p className="mt-1 font-semibold">{formatter.format(property.price)}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">ROI</p>
            <p className="mt-1 font-semibold">{property.roi}%</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Trust</p>
            <p className="mt-1 font-semibold">{property.trustScore}/100</p>
          </div>
        </div>

        <div className="h-1.5 overflow-hidden rounded-full bg-secondary">
          <div
            className="h-full rounded-full bg-primary"
            style={{ width: `${property.trustScore}%` }}
          />
        </div>
      </CardContent>
    </Card>
  );
}

export default function MarketplacePage() {
  const [liveProperties, setLiveProperties] = useState<Property[]>([]);
  const [liveError, setLiveError] = useState<string | null>(null);
  const [priceRange, setPriceRange] = useState([400000, 1400000]);
  const [selectedLocations, setSelectedLocations] = useState<string[]>(locations);
  const [minTrustScore, setMinTrustScore] = useState([70]);
  const [verifiedOnly, setVerifiedOnly] = useState(false);
  const [sortBy, setSortBy] = useState<SortOption>("price");
  const catalog = liveProperties.length > 0 ? liveProperties : properties;
  const availableLocations = useMemo(() => Array.from(new Set(catalog.map((property) => property.location))), [catalog]);

  useEffect(() => {
    let ignore = false;
    fetchRecommendations({ budget: 1400000, roi_goal: 7, verified_only: false })
      .then((payload) => {
        if (ignore) return;
        const mapped = payload.recommendations.map((item) => ({
          id: String(item.property.external_id ?? item.property.id),
          title: item.property.title,
          price: Number(item.property.price_numeric ?? 0),
          location: item.property.location,
          roi: item.investment_advisor.roi_prediction,
          trustScore: item.investment_advisor.trust_score.score,
          isVerified: Boolean(item.property.blockchain_verified || item.property.verified_status)
        })).filter((item) => item.price > 0);
        setLiveProperties(mapped);
        if (mapped.length > 0) {
          setSelectedLocations(Array.from(new Set(mapped.map((item) => item.location))));
          const prices = mapped.map((item) => item.price);
          setPriceRange([Math.min(...prices), Math.max(...prices)]);
        }
      })
      .catch((error) => {
        if (!ignore) setLiveError(getApiErrorMessage(error));
      });
    return () => {
      ignore = true;
    };
  }, []);

  const visibleProperties = useMemo(() => {
    return catalog
      .filter((property) => property.price >= priceRange[0] && property.price <= priceRange[1])
      .filter((property) => selectedLocations.includes(property.location))
      .filter((property) => property.trustScore >= minTrustScore[0])
      .filter((property) => (verifiedOnly ? property.isVerified : true))
      .sort((a, b) => {
        if (sortBy === "price") return a.price - b.price;
        if (sortBy === "roi") return b.roi - a.roi;
        return b.trustScore - a.trustScore;
      });
  }, [catalog, minTrustScore, priceRange, selectedLocations, sortBy, verifiedOnly]);

  function toggleLocation(location: string) {
    setSelectedLocations((current) =>
      current.includes(location)
        ? current.filter((item) => item !== location)
        : [...current, location]
    );
  }

  return (
    <main className="min-h-screen bg-background px-6 py-10 md:px-10">
      <div className="mx-auto max-w-7xl">
        <div className="mb-10 flex flex-col justify-between gap-6 md:flex-row md:items-end">
          <div className="space-y-3">
            <div className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1 text-xs font-medium text-muted-foreground">
              <SlidersHorizontal className="h-3.5 w-3.5" />
              Curated Marketplace
            </div>
            <div>
              <h1 className="text-3xl font-semibold tracking-normal md:text-4xl">
                Investment-grade properties
              </h1>
              <p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground">
                Filter by price, location, verification, and trust signals with a clean split-view workspace.
              </p>
            </div>
          </div>

          <div className="w-full md:w-56">
            <Select value={sortBy} onValueChange={(value) => setSortBy(value as SortOption)}>
              <SelectTrigger aria-label="Sort properties">
                <SelectValue placeholder="Sort By" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="price">Price</SelectItem>
                <SelectItem value="roi">ROI</SelectItem>
                <SelectItem value="trustScore">Trust Score</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="grid gap-8 lg:grid-cols-[minmax(260px,25%)_1fr]">
          <aside className="lg:sticky lg:top-8 lg:self-start">
            <Card className="border-border/70 bg-card/95 shadow-none">
              <CardContent className="p-0">
                <ScrollArea className="h-auto max-h-[calc(100vh-4rem)] px-6">
                  <Accordion
                    type="multiple"
                    defaultValue={["price", "location", "trust"]}
                    className="w-full"
                  >
                    <AccordionItem value="price">
                      <AccordionTrigger>Price Range</AccordionTrigger>
                      <AccordionContent className="space-y-4">
                        <Slider
                          min={350000}
                          max={1400000}
                          step={10000}
                          value={priceRange}
                          onValueChange={setPriceRange}
                        />
                        <div className="flex items-center justify-between text-xs text-muted-foreground">
                          <span>{formatter.format(priceRange[0])}</span>
                          <span>{formatter.format(priceRange[1])}</span>
                        </div>
                      </AccordionContent>
                    </AccordionItem>

                    <AccordionItem value="location">
                      <AccordionTrigger>Location</AccordionTrigger>
                      <AccordionContent className="space-y-3">
                        {availableLocations.map((location) => (
                          <label
                            key={location}
                            className="flex cursor-pointer items-center gap-3 rounded-md py-1 text-sm"
                          >
                            <Checkbox
                              checked={selectedLocations.includes(location)}
                              onCheckedChange={() => toggleLocation(location)}
                            />
                            <span>{location}</span>
                          </label>
                        ))}
                      </AccordionContent>
                    </AccordionItem>

                    <AccordionItem value="trust">
                      <AccordionTrigger>Trust Score</AccordionTrigger>
                      <AccordionContent className="space-y-4">
                        <Slider
                          min={0}
                          max={100}
                          step={1}
                          value={minTrustScore}
                          onValueChange={setMinTrustScore}
                        />
                        <div className="flex items-center justify-between text-xs text-muted-foreground">
                          <span>Minimum</span>
                          <span>{minTrustScore[0]}/100</span>
                        </div>
                      </AccordionContent>
                    </AccordionItem>
                  </Accordion>

                  <div className="flex items-center justify-between py-5">
                    <div>
                      <p className="text-sm font-medium">Verified Only</p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        Show audited listings
                      </p>
                    </div>
                    <Switch checked={verifiedOnly} onCheckedChange={setVerifiedOnly} />
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </aside>

          <section className="min-w-0">
            <div className="mb-5 flex items-center justify-between text-sm text-muted-foreground">
              <span>
                {visibleProperties.length} properties
                {liveProperties.length > 0 ? " from smart recommendations" : ""}
              </span>
              <span className="inline-flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                Sorted by {sortBy === "trustScore" ? "Trust Score" : sortBy.toUpperCase()}
              </span>
            </div>
            {liveError && (
              <p className="mb-4 rounded-lg border border-amber-400/20 bg-amber-400/10 px-4 py-3 text-sm text-amber-200">
                {liveError}
              </p>
            )}

            <motion.div layout className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
              <AnimatePresence mode="popLayout">
                {visibleProperties.map((property) => (
                  <motion.div
                    key={property.id}
                    layout
                    initial={{ opacity: 0, y: 18 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 18, scale: 0.98 }}
                    transition={{ duration: 0.24, ease: "easeOut" }}
                  >
                    <PropertyCard property={property} />
                  </motion.div>
                ))}
              </AnimatePresence>
            </motion.div>

            <div
              className={cn(
                "mt-16 rounded-lg border border-dashed border-border bg-card/60 p-10 text-center text-sm text-muted-foreground",
                visibleProperties.length > 0 && "hidden"
              )}
            >
              No properties match the current filters.
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
