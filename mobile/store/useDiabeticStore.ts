/** Zustand store del perfil diabético.
 *
 * `profile === null` con `isLoaded === true` significa "el usuario no tiene
 * perfil" (modo diabético inactivo). Mientras `isLoaded === false`, la UI
 * debe mostrar un loader.
 */

import { create } from "zustand";
import * as API from "../services/diabeticProfile";
import type { DiabeticProfile, DiabeticProfileUpsert } from "../types";

interface DiabeticStore {
  profile: DiabeticProfile | null;
  isLoaded: boolean;
  isSaving: boolean;

  load: () => Promise<void>;
  save: (data: DiabeticProfileUpsert) => Promise<DiabeticProfile>;
  deactivate: () => Promise<void>;
  reset: () => void;
}

export const useDiabeticStore = create<DiabeticStore>((set) => ({
  profile: null,
  isLoaded: false,
  isSaving: false,

  load: async () => {
    const profile = await API.getProfile();
    set({ profile, isLoaded: true });
  },

  save: async (data) => {
    set({ isSaving: true });
    try {
      const profile = await API.upsertProfile(data);
      set({ profile, isLoaded: true });
      return profile;
    } finally {
      set({ isSaving: false });
    }
  },

  deactivate: async () => {
    await API.deleteProfile();
    set({ profile: null });
  },

  reset: () => set({ profile: null, isLoaded: false, isSaving: false }),
}));
