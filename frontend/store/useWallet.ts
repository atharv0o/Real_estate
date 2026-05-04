"use client";

import { PeraWalletConnect } from "@perawallet/connect";
import { create } from "zustand";

const peraWallet =
  typeof window !== "undefined" ? new PeraWalletConnect() : null;

type WalletState = {
  userAddress: string | null;
  isConnected: boolean;
  isConnecting: boolean;
  hasInitialized: boolean;
  connectWallet: () => Promise<void>;
  disconnectWallet: () => Promise<void>;
  initializeWalletSession: () => Promise<void>;
};

function getPrimaryAddress(accounts: string[]) {
  return accounts.length > 0 ? accounts[0] : null;
}

function bindDisconnectHandler(set: (state: Partial<WalletState>) => void) {
  peraWallet?.connector?.on("disconnect", () => {
    set({ userAddress: null, isConnected: false });
  });
}

export function truncateAddress(address: string | null) {
  if (!address) return "";
  return `${address.slice(0, 4)}...${address.slice(-4)}`;
}

export const useWallet = create<WalletState>((set, get) => ({
  userAddress: null,
  isConnected: false,
  isConnecting: false,
  hasInitialized: false,

  connectWallet: async () => {
    if (!peraWallet || get().isConnecting) return;

    try {
      set({ isConnecting: true });
      const accounts = await peraWallet.connect();
      const userAddress = getPrimaryAddress(accounts);

      set({
        userAddress,
        isConnected: Boolean(userAddress),
        hasInitialized: true
      });
      bindDisconnectHandler(set);
    } finally {
      set({ isConnecting: false });
    }
  },

  disconnectWallet: async () => {
    if (!peraWallet) return;

    await peraWallet.disconnect();
    set({
      userAddress: null,
      isConnected: false,
      isConnecting: false,
      hasInitialized: true
    });
  },

  initializeWalletSession: async () => {
    if (!peraWallet || get().hasInitialized) return;

    try {
      set({ isConnecting: true });
      const accounts = await peraWallet.reconnectSession();
      const userAddress = getPrimaryAddress(accounts);

      set({
        userAddress,
        isConnected: Boolean(userAddress),
        hasInitialized: true
      });

      if (userAddress) bindDisconnectHandler(set);
    } catch {
      set({
        userAddress: null,
        isConnected: false,
        hasInitialized: true
      });
    } finally {
      set({ isConnecting: false });
    }
  }
}));
