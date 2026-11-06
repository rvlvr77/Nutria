import { ApiError, apiFetch } from "@/lib/api";

export const dynamic = "force-dynamic";

interface Liveness {
  status: "ok";
  app: string;
  version: string;
  environment: string;
}

async function getBackendStatus(): Promise<{ ok: true; data: Liveness } | { ok: false; reason: string }> {
  try {
    const data = await apiFetch<Liveness>("/health", { cache: "no-store", timeoutMs: 3_000 });
    return { ok: true, data };
  } catch (err) {
    return { ok: false, reason: err instanceof ApiError ? err.message : "Error desconocido" };
  }
}

export default async function HomePage() {
  const status = await getBackendStatus();

  return (
    <main id="main" className="container flex min-h-screen flex-col justify-center gap-8 py-16">
      <header className="space-y-3">
        <h1 className="text-4xl font-bold tracking-tight">NutriAI</h1>
        <p className="max-w-xl text-lg text-muted-foreground">
          Planes de alimentación personalizados con el Sistema Mexicano de Alimentos Equivalentes
          (SMAE) y FoodData Central del USDA.
        </p>
      </header>

      <section aria-labelledby="status-title" className="max-w-md rounded-lg border bg-card p-5">
        <h2 id="status-title" className="mb-2 font-semibold">
          Estado del sistema
        </h2>
        <p role="status" data-testid="backend-status" className="flex items-center gap-2">
          <span
            aria-hidden="true"
            className={`inline-block h-3 w-3 rounded-full ${status.ok ? "bg-adherence-good" : "bg-adherence-bad"}`}
          />
          {status.ok
            ? `API en línea · v${status.data.version} (${status.data.environment})`
            : `API no disponible: ${status.reason}`}
        </p>
      </section>

      <footer className="space-y-1 text-sm text-muted-foreground">
        <p>Esta app no sustituye la consulta con un profesional de la salud.</p>
        <p>Datos nutricionales: FoodData Central, USDA · SMAE (uso educativo).</p>
      </footer>
    </main>
  );
}
