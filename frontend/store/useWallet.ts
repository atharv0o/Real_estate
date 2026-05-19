"use client";

import { PeraWalletConnect } from "@perawallet/connect";
import { create } from "zustand";

const peraWallet =
  typeof window !== "undefined" ? new PeraWalletConnect() : null;

let disconnectHandlerBoundTo: unknown = null;

type WalletState = {
  walletAddress: string | null;
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
  const connector = peraWallet?.connector;

  if (!connector || connector === disconnectHandlerBoundTo) return;

  connector.on("disconnect", () => {
    set({ walletAddress: null, userAddress: null, isConnected: false });
  });
  disconnectHandlerBoundTo = connector;
}

export function truncateAddress(address: string | null) {
  if (!address) return "";
  return `${address.slice(0, 4)}...${address.slice(-4)}`;
}

export const useWallet = create<WalletState>((set, get) => ({
  walletAddress: null,
  userAddress: null,
  isConnected: false,
  isConnecting: false,
  hasInitialized: false,

  connectWallet: async () => {
    if (!peraWallet || get().isConnecting) return;

    try {
      set({ isConnecting: true });
      const accounts = await peraWallet.connect();
      const walletAddress = getPrimaryAddress(accounts);

      set({
        walletAddress,
        userAddress: walletAddress,
        isConnected: Boolean(walletAddress),
        hasInitialized: true
      });
      bindDisconnectHandler(set);
    } catch (error) {
      console.warn("Pera wallet connection failed or was cancelled.", error);
      set({
        walletAddress: null,
        userAddress: null,
        isConnected: false,
        hasInitialized: true
      });
    } finally {
      set({ isConnecting: false });
    }
  },

  disconnectWallet: async () => {
    if (!peraWallet) {
      set({
        walletAddress: null,
        userAddress: null,
        isConnected: false,
        isConnecting: false,
        hasInitialized: true
      });
      return;
    }

    try {
      await peraWallet.disconnect();
    } catch (error) {
      console.warn("Pera wallet disconnect failed.", error);
    } finally {
      set({
        walletAddress: null,
        userAddress: null,
        isConnected: false,
        isConnecting: false,
        hasInitialized: true
      });
    }
  },

  initializeWalletSession: async () => {
    if (!peraWallet || get().hasInitialized) return;

    try {
      set({ isConnecting: true });
      const accounts = await peraWallet.reconnectSession();
      const walletAddress = getPrimaryAddress(accounts);

      set({
        walletAddress,
        userAddress: walletAddress,
        isConnected: Boolean(walletAddress),
        hasInitialized: true
      });

      if (walletAddress) bindDisconnectHandler(set);
    } catch (error) {
      console.warn("Pera wallet session reconnect failed.", error);
      set({
        walletAddress: null,
        userAddress: null,
        isConnected: false,
        hasInitialized: true
      });
    } finally {
      set({ isConnecting: false });
    }
  }
}));
