"use client";

import { useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  BadgeCheck,
  Check,
  ChevronLeft,
  ChevronRight,
  FileCheck2,
  Loader2,
  Shield,
  Terminal,
  Upload,
  Wallet
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import { truncateAddress, useWallet } from "@/store/useWallet";

const steps = [
  { id: 1, title: "Details", description: "Property metadata" },
  { id: 2, title: "Documents", description: "Proof package" },
  { id: 3, title: "Blockchain", description: "Review & Mint" }
];

const mintLogs = [
  "Calculating document SHA-256 hash...",
  "Hashing property metadata...",
  "Sending transaction to Algorand Testnet...",
  "Success! Asset ID: #ALG-7729-X"
];

export default function SellerDashboardPage() {
  const [activeStep, setActiveStep] = useState(1);
  const [title, setTitle] = useState("Skyline Residences");
  const [price, setPrice] = useState("720000");
  const [location, setLocation] = useState("Worli, Mumbai");
  const [fileName, setFileName] = useState("ownership-pack.pdf");
  const [isMinting, setIsMinting] = useState(false);
  const [progress, setProgress] = useState(0);
  const [visibleLogCount, setVisibleLogCount] = useState(0);
  const {
    connectWallet,
    disconnectWallet,
    isConnected,
    isConnecting,
    userAddress
  } = useWallet();

  const canGoBack = activeStep > 1;
  const canGoNext = activeStep < steps.length;

  const summaryPrice = useMemo(
    () =>
      new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        maximumFractionDigits: 0
      }).format(Number(price || 0)),
    [price]
  );

  function handleDrop(event: React.DragEvent<HTMLLabelElement>) {
    event.preventDefault();
    const droppedFile = event.dataTransfer.files?.[0];
    if (droppedFile) setFileName(droppedFile.name);
  }

  function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const selectedFile = event.target.files?.[0];
    if (selectedFile) setFileName(selectedFile.name);
  }

  function handleMint() {
    if (isMinting || !isConnected) return;

    setIsMinting(true);
    setProgress(0);
    setVisibleLogCount(0);

    mintLogs.forEach((_, index) => {
      window.setTimeout(() => {
        setVisibleLogCount(index + 1);
        setProgress(Math.round(((index + 1) / mintLogs.length) * 100));
      }, 650 * (index + 1));
    });

    window.setTimeout(() => {
      setIsMinting(false);
    }, 650 * mintLogs.length + 450);
  }

  return (
    <div className="pb-10 text-slate-100">
      <div className="mb-8 flex flex-col justify-between gap-5 md:flex-row md:items-end">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-300">
            <Shield className="h-3.5 w-3.5" />
            Seller Dashboard
          </div>
          <h1 className="mt-4 font-display text-3xl font-semibold tracking-normal text-white md:text-5xl">
            List and mint verified property assets
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">
            Package listing metadata, legal documents, and Algorand Testnet minting into one controlled seller workflow.
          </p>
        </div>

        <Button
          variant="outline"
          className={cn(
            "border-white/10 bg-slate-950/70 text-white hover:bg-emerald-500/10",
            isConnected &&
              "border-emerald-400/30 text-emerald-200 shadow-[0_0_34px_rgba(16,185,129,0.18)]"
          )}
          disabled={isConnecting}
          onClick={isConnected ? disconnectWallet : connectWallet}
          title={isConnected ? "Disconnect Pera Wallet" : "Connect Pera Wallet"}
        >
          <Wallet className="h-4 w-4 text-emerald-400" />
          <AnimatePresence mode="wait" initial={false}>
            <motion.span
              key={isConnected ? userAddress : "connect"}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.18 }}
            >
              {isConnecting
                ? "Connecting..."
                : isConnected
                  ? truncateAddress(userAddress)
                  : "Connect Pera Wallet"}
            </motion.span>
          </AnimatePresence>
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_420px]">
        <motion.section
          animate={{
            boxShadow: isMinting
              ? "0 0 80px rgba(16,185,129,0.28)"
              : "0 24px 80px rgba(15,23,42,0.14)"
          }}
          className="rounded-lg"
        >
          <Card className="border-white/10 bg-slate-950/75 text-white shadow-none backdrop-blur-xl">
            <CardContent className="p-6 md:p-8">
              <div className="grid gap-8 lg:grid-cols-[240px_1fr]">
                <div className="space-y-3">
                  {steps.map((step) => {
                    const isActive = step.id === activeStep;
                    const isComplete = step.id < activeStep;

                    return (
                      <button
                        key={step.id}
                        className={cn(
                          "flex w-full items-center gap-4 rounded-lg border p-4 text-left transition-colors",
                          isActive
                            ? "border-emerald-500/40 bg-emerald-500/10"
                            : "border-white/10 bg-white/[0.03] hover:bg-white/[0.06]"
                        )}
                        onClick={() => setActiveStep(step.id)}
                      >
                        <span
                          className={cn(
                            "grid h-9 w-9 place-items-center rounded-full border text-sm font-semibold",
                            isComplete
                              ? "border-emerald-500 bg-emerald-500 text-slate-950"
                              : isActive
                                ? "border-emerald-400 text-emerald-300"
                                : "border-white/15 text-slate-400"
                          )}
                        >
                          {isComplete ? <Check className="h-4 w-4" /> : step.id}
                        </span>
                        <span>
                          <span className="block text-sm font-medium text-white">{step.title}</span>
                          <span className="text-xs text-slate-500">{step.description}</span>
                        </span>
                      </button>
                    );
                  })}
                </div>

                <div className="min-h-[430px]">
                  <AnimatePresence mode="wait">
                    {activeStep === 1 && (
                      <motion.div
                        key="details"
                        initial={{ opacity: 0, x: 18 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -18 }}
                        transition={{ duration: 0.22 }}
                        className="space-y-5"
                      >
                        <div>
                          <h2 className="text-xl font-semibold">Property Details</h2>
                          <p className="mt-1 text-sm text-slate-400">
                            These fields become the asset metadata payload.
                          </p>
                        </div>
                        <label className="block space-y-2">
                          <span className="text-sm font-medium">Title</span>
                          <Input value={title} onChange={(event) => setTitle(event.target.value)} />
                        </label>
                        <label className="block space-y-2">
                          <span className="text-sm font-medium">Price</span>
                          <Input
                            inputMode="numeric"
                            value={price}
                            onChange={(event) => setPrice(event.target.value)}
                          />
                        </label>
                        <label className="block space-y-2">
                          <span className="text-sm font-medium">Location</span>
                          <Input
                            value={location}
                            onChange={(event) => setLocation(event.target.value)}
                          />
                        </label>
                      </motion.div>
                    )}

                    {activeStep === 2 && (
                      <motion.div
                        key="documents"
                        initial={{ opacity: 0, x: 18 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -18 }}
                        transition={{ duration: 0.22 }}
                        className="space-y-5"
                      >
                        <div>
                          <h2 className="text-xl font-semibold">Documents</h2>
                          <p className="mt-1 text-sm text-slate-400">
                            Upload proof of ownership, tax records, and zoning clearance.
                          </p>
                        </div>
                        <Card className="border-dashed border-white/15 bg-white/[0.03] shadow-none">
                          <CardContent className="p-0">
                            <label
                              className="flex min-h-72 cursor-pointer flex-col items-center justify-center gap-4 rounded-lg p-8 text-center"
                              onDragOver={(event) => event.preventDefault()}
                              onDrop={handleDrop}
                            >
                              <span className="grid h-16 w-16 place-items-center rounded-full bg-emerald-500/10 text-emerald-300">
                                <Upload className="h-7 w-7" />
                              </span>
                              <span>
                                <span className="block text-base font-medium text-white">
                                  Drop documents here
                                </span>
                                <span className="mt-1 block text-sm text-slate-400">
                                  PDF, PNG, or ZIP legal packs supported
                                </span>
                              </span>
                              <input
                                type="file"
                                className="sr-only"
                                onChange={handleFileChange}
                              />
                            </label>
                          </CardContent>
                        </Card>
                        <div className="flex items-center gap-3 rounded-lg border border-emerald-500/20 bg-emerald-500/10 p-4 text-sm text-emerald-100">
                          <FileCheck2 className="h-5 w-5" />
                          {fileName}
                        </div>
                      </motion.div>
                    )}

                    {activeStep === 3 && (
                      <motion.div
                        key="blockchain"
                        initial={{ opacity: 0, x: 18 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -18 }}
                        transition={{ duration: 0.22 }}
                        className="space-y-5"
                      >
                        <div>
                          <h2 className="text-xl font-semibold">Review & Mint</h2>
                          <p className="mt-1 text-sm text-slate-400">
                            Confirm the payload before creating the mock Algorand asset.
                          </p>
                        </div>
                        <div className="grid gap-3 sm:grid-cols-2">
                          {[
                            ["Title", title],
                            ["Price", summaryPrice],
                            ["Location", location],
                            ["Document", fileName]
                          ].map(([label, value]) => (
                            <div
                              key={label}
                              className="rounded-lg border border-white/10 bg-white/[0.03] p-4"
                            >
                              <p className="text-xs text-slate-500">{label}</p>
                              <p className="mt-1 text-sm font-medium text-white">{value}</p>
                            </div>
                          ))}
                        </div>
                        <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/10 p-4 text-sm text-emerald-100">
                          Metadata will be hashed locally before the mock mint transaction is sent to Algorand Testnet.
                        </div>
                        <Button
                          className="w-full bg-emerald-500 text-slate-950 hover:bg-emerald-400"
                          onClick={handleMint}
                          disabled={isMinting || !isConnected}
                          title={!isConnected ? "Please Connect Wallet" : "Mint property NFT"}
                        >
                          {isMinting ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <BadgeCheck className="h-4 w-4" />
                          )}
                          {isConnected ? "Mint" : "Please Connect Wallet"}
                        </Button>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </div>

              <div className="mt-8 flex items-center justify-between border-t border-white/10 pt-5">
                <Button
                  variant="outline"
                  className="border-white/10 bg-white/5 text-white hover:bg-white/10"
                  disabled={!canGoBack}
                  onClick={() => setActiveStep((step) => Math.max(1, step - 1))}
                >
                  <ChevronLeft className="h-4 w-4" />
                  Back
                </Button>
                <Button
                  className="bg-emerald-500 text-slate-950 hover:bg-emerald-400"
                  disabled={!canGoNext}
                  onClick={() => setActiveStep((step) => Math.min(steps.length, step + 1))}
                >
                  Next
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.section>

        <aside className="space-y-6">
          <Card className="border-white/10 bg-black text-emerald-400 shadow-none">
            <CardContent className="p-0">
              <div className="flex items-center gap-2 border-b border-emerald-500/20 px-5 py-4">
                <Terminal className="h-4 w-4" />
                <span className="font-mono text-xs uppercase tracking-[0.2em]">
                  Blockchain Console
                </span>
              </div>
              <div className="min-h-72 space-y-3 p-5 font-mono text-sm leading-6">
                <AnimatePresence>
                  {mintLogs.slice(0, visibleLogCount).map((log) => (
                    <motion.p
                      key={log}
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0 }}
                      className="text-emerald-400"
                    >
                      <span className="text-emerald-700">$</span> {log}
                    </motion.p>
                  ))}
                </AnimatePresence>
                {visibleLogCount === 0 && (
                  <p className="text-emerald-700">
                    $ Awaiting mint command...
                  </p>
                )}
              </div>
            </CardContent>
          </Card>

          <Card className="border-white/10 bg-slate-950/75 text-white shadow-none backdrop-blur-xl">
            <CardContent className="space-y-4 p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">Algorand confirmation</p>
                  <p className="mt-1 text-xs text-slate-500">Mock block finality timer</p>
                </div>
                <span className="text-sm text-emerald-300">{progress}%</span>
              </div>
              <Progress value={progress} />
              <p className="text-xs text-slate-500">
                {progress === 100
                  ? "Asset confirmed on mock Testnet ledger."
                  : "Progress appears after you click Mint."}
              </p>
            </CardContent>
          </Card>
        </aside>
      </div>
    </div>
  );
}
