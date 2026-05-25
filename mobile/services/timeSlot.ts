/** Helpers de franjas horarias del perfil diabético (Opción A: 3 fijas).
 *
 * Las franjas son las acordadas con el usuario (España):
 *   desayuno 00:00 – 11:00
 *   comida   11:00 – 17:00
 *   cena     17:00 – 24:00
 *
 * El backend usa el `slot` enviado por el cliente (no recomputa por hora
 * del servidor) — la elección del usuario manda.
 */

import type { TimeSlot } from "../types";

export const TIME_SLOT_LABELS: Record<TimeSlot, string> = {
  breakfast: "Desayuno",
  lunch: "Comida",
  dinner: "Cena",
};

export function currentSlot(now: Date = new Date()): TimeSlot {
  const h = now.getHours();
  if (h < 11) return "breakfast";
  if (h < 17) return "lunch";
  return "dinner";
}
