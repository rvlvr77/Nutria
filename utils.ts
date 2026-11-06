import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/** Helper estándar de shadcn/ui para combinar clases Tailwind. */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
