"use client";

import { useEffect } from "react";
import Link from "next/link";
import { AnimatePresence, motion } from "framer-motion";
import { Landmark, Wallet } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/ThemeToggle";
import { cn } from "@/lib/utils";
import { truncateAddress, useWallet } from "@/store/useWallet";

const links = [
  { href: "/marketplace", label: "Marketplace" },
  { href: "/seller", label: "Dashboard" },
  { href: "/analytics", label: "Analytics" }
];

export function Navbar() {
  const {
    connectWallet,
    disconnectWallet,
    initializeWalletSession,
    isConnected,
    isConnecting,
    userAddress
  } = useWallet();

  useEffect(() => {
    initializeWalletSession();
  }, [initializeWalletSession]);

  return (
    <header className="sticky top-0 z-50 border-b border-border/70 bg-background/55 backdrop-blur-2xl supports-[backdrop-filter]:bg-background/45">
      <div className="mx-auto flex h-20 w-full max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-full border border-emerald-500/25 bg-emerald-500/10 text-emerald-500 shadow-[0_0_40px_rgba(16,185,129,0.16)]">
            <Landmark className="h-5 w-5" />
          </span>
          <span className="font-display text-base font-semibold tracking-tight text-foreground sm:text-lg">
            RealEstate<span className="text-blue-600">AI</span>
          </span>
        </Link>

        <nav className="relative z-[100] hidden items-center gap-1 rounded-full border border-border bg-background/50 p-1 shadow-glass backdrop-blur-xl md:flex">
          {links.map((link) => (
            <motion.div
              key={link.href}
              whileHover={{ scale: 1.04 }}
              whileTap={{ scale: 0.98 }}
              transition={{ type: "spring", stiffness: 420, damping: 28 }}
            >
              <Button asChild variant="ghost" size="sm">
                <Link href={link.href}>{link.label}</Link>
              </Button>
            </motion.div>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <ThemeToggle />
          <Button
            className={cn(
              "hidden text-white sm:inline-flex",
              isConnected
                ? "border border-emerald-400/30 bg-emerald-500/15 text-emerald-200 shadow-[0_0_34px_rgba(16,185,129,0.22)] hover:bg-emerald-500/20"
                : "bg-blue-600 hover:bg-blue-600/90"
            )}
            disabled={isConnecting}
            onClick={isConnected ? disconnectWallet : connectWallet}
            title={isConnected ? "Disconnect Pera Wallet" : "Connect Pera Wallet"}
          >
            <Wallet className="h-4 w-4" />
            <AnimatePresence mode="wait" initial={false}>
              <motion.span
                key={isConnected ? userAddress : "connect-wallet"}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.18 }}
              >
                {isConnecting
                  ? "Connecting..."
                  : isConnected
                    ? truncateAddress(userAddress)
                    : "Connect Wallet"}
              </motion.span>
            </AnimatePresence>
          </Button>
        </div>
      </div>
    </header>
  );
}
