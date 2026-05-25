/** Zustand store para estado de autenticación. */

import { create } from "zustand";
import * as AuthAPI from "../services/auth";
import { configureAuth } from "../services/api";
import { clearToken, getToken, saveToken } from "../services/tokenStorage";
import { useDiabeticStore } from "./useDiabeticStore";
import type { User } from "../types";

interface AuthStore {
  token: string | null;
  user: User | null;
  isLoading: boolean;
  isInitialized: boolean;

  initialize: () => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, emailConfirm: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshMe: () => Promise<void>;
}

export const useAuthStore = create<AuthStore>((set, get) => ({
  token: null,
  user: null,
  isLoading: false,
  isInitialized: false,

  initialize: async () => {
    // Wire axios interceptor al token vivo del store y al logout on-401.
    configureAuth({
      getToken: () => get().token,
      onUnauthorized: () => {
        void get().logout();
      },
    });

    const stored = await getToken();
    if (!stored) {
      set({ isInitialized: true });
      return;
    }
    set({ token: stored });
    try {
      const user = await AuthAPI.me();
      set({ user, isInitialized: true });
    } catch {
      await clearToken();
      set({ token: null, user: null, isInitialized: true });
    }
  },

  login: async (email, password) => {
    set({ isLoading: true });
    try {
      const session = await AuthAPI.login(email, password);
      await saveToken(session.token);
      set({ token: session.token, user: session.user });
    } finally {
      set({ isLoading: false });
    }
  },

  register: async (email, emailConfirm, password) => {
    set({ isLoading: true });
    try {
      await AuthAPI.register(email, emailConfirm, password);
    } finally {
      set({ isLoading: false });
    }
  },

  logout: async () => {
    await clearToken();
    set({ token: null, user: null });
    // Resetear stores que cachean datos del usuario para que no haya
    // fugas entre sesiones (p. ej. distinto usuario en la misma web).
    useDiabeticStore.getState().reset();
  },

  refreshMe: async () => {
    const user = await AuthAPI.me();
    set({ user });
  },
}));
