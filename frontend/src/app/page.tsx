"use client";

import * as React from "react";
import MineSafetyDashboard from "@/components/mine-safety-dashboard";
import Link from "next/link";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Progress } from "@/components/ui/progress";
import { Card } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";
import { Wifi, Cpu, ShieldAlert, Settings, Bell } from "lucide-react";

type AlertItem = {
  id: string;
  level: "safe" | "warning" | "danger";
  message: string;
  time: string;
  acknowledged?: boolean;
};

export default function Page() {
  const sites = React.useMemo(
    () => [
      { id: "north-pit", name: "North Pit" },
      { id: "south-tunnel", name: "South Tunnel" },
      { id: "west-slope", name: "West Slope" },
    ],
    []
  );
  const [selectedSite, setSelectedSite] = React.useState<string>(sites[0].id);
  const [maintenanceMode, setMaintenanceMode] = React.useState(false);
  const [notifyOps, setNotifyOps] = React.useState(true);
  const [systemOnline, setSystemOnline] = React.useState(true);
  const [networkQuality, setNetworkQuality] = React.useState<"good" | "degraded" | "down">("good");
  const [aiModelReady, setAiModelReady] = React.useState(true);
  const [appRiskBaseline, setAppRiskBaseline] = React.useState(28);
  const [lightMode, setLightMode] = React.useState(false);

  // FastAPI live endpoints state
  const FASTAPI_BASE = "http://localhost:8000";
  const [vibrationLive, setVibrationLive] = React.useState<null | { accelerometer: number; geophone: number; seismometer: number; timestamp: number }>(null);
  const [displacementLive, setDisplacementLive] = React.useState<null | { crack: number; inclinometer: number; extensometer: number; timestamp: number }>(null);
  const [hydroLive, setHydroLive] = React.useState<null | { moisture: number; piezometer: number; timestamp: number }>(null);
  const [environmentLive, setEnvironmentLive] = React.useState<null | { rain: number; timestamp: number }>(null);
  const [riskLevelLive, setRiskLevelLive] = React.useState<null | "LOW" | "MEDIUM" | "HIGH" >(null);

  const sensorsBySite: Record<string, string[]> = React.useMemo(
    () => ({
      "north-pit": ["S-AX01", "S-AX02", "S-TMP03", "S-VIB07", "S-TLT09"],
      "south-tunnel": ["S-AX11", "S-AX12", "S-TMP13", "S-VIB17"],
      "west-slope": ["S-AX21", "S-TLT22", "S-TMP23", "S-VIB27", "S-VIB28", "S-AX24"],
    }),
    []
  );

  // Simulated sensor readings for the sensor grid
  const [sensorData, setSensorData] = React.useState<Record<string, { temp: number; vib: number; tilt: number; battery: number }>>({});
  React.useEffect(() => {
    const ids = sensorsBySite[selectedSite] ?? [];
    // initialize
    setSensorData(
      Object.fromEntries(
        ids.map((id) => [
          id,
          { temp: 18 + Math.random() * 14, vib: Math.random() * 5, tilt: Math.random() * 2, battery: 60 + Math.random() * 40 },
        ])
      )
    );
    const t = setInterval(() => {
      setSensorData((prev) =>
        Object.fromEntries(
          ids.map((id) => {
            const p = prev[id] ?? { temp: 24, vib: 1, tilt: 0.5, battery: 90 };
            return [
              id,
              {
                temp: Math.max(10, Math.min(40, p.temp + (Math.random() - 0.5))),
                vib: Math.max(0, Math.min(10, p.vib + (Math.random() - 0.5))),
                tilt: Math.max(0, Math.min(5, p.tilt + (Math.random() - 0.5) * 0.2)),
                battery: Math.max(5, p.battery - Math.random() * 0.3),
              },
            ];
          })
        )
      );
    }, 2000);
    return () => clearInterval(t);
  }, [selectedSite, sensorsBySite]);

  // Live polling from FastAPI (every 3s)
  React.useEffect(() => {
    let aborted = false;
    let timer: ReturnType<typeof setInterval> | undefined;

    const pollOnce = async () => {
      try {
        const [vRes, dRes, hRes, eRes, rRes] = await Promise.all([
          fetch(`${FASTAPI_BASE}/sensor/sesmic`),
          fetch(`${FASTAPI_BASE}/sensor/displacement`),
          fetch(`${FASTAPI_BASE}/sensor/hydro`),
          fetch(`${FASTAPI_BASE}/sensor/environment`),
          fetch(`${FASTAPI_BASE}/risk-level`),
        ]);
        if (aborted) return;
        const [vJ, dJ, hJ, eJ, rJ] = await Promise.all([
          vRes.json(),
          dRes.json(),
          hRes.json(),
          eRes.json(),
          rRes.json(),
        ]);
        if (aborted) return;
        setVibrationLive(vJ);
        setDisplacementLive(dJ);
        setHydroLive(hJ);
        setEnvironmentLive(eJ);
        const computed = computeRiskFromLive(vJ, dJ, eJ);
        setRiskLevelLive((rJ?.risk_level as any) ?? computed);
      } catch (_) {
        // swallow errors for MVP polling
      }
    };

    pollOnce();
    timer = setInterval(pollOnce, 3000);

    return () => {
      aborted = true;
      if (timer) clearInterval(timer);
    };
  }, []);

  const seedAlerts: AlertItem[] = React.useMemo(
    () => [
      {
        id: "A-1027",
        level: "warning",
        message: "Vibration spike detected near north slope.",
        time: "5m ago",
      },
      {
        id: "A-1026",
        level: "safe",
        message: "All systems normal.",
        time: "22m ago",
      },
      {
        id: "A-1025",
        level: "danger",
        message: "Accelerometer anomaly at tunnel B.",
        time: "1h ago",
      },
    ],
    []
  );

  const siteSensors = sensorsBySite[selectedSite] ?? [];
  const unresolvedAlerts = React.useMemo(
    () => seedAlerts.filter((a) => a.level !== "safe" && !a.acknowledged).length,
    [seedAlerts]
  );

  const systemHealth = React.useMemo(() => {
    let score = 100;
    if (!systemOnline) score -= 40;
    if (!aiModelReady) score -= 20;
    if (networkQuality === "degraded") score -= 15;
    if (networkQuality === "down") score -= 45;
    if (maintenanceMode) score -= 10;
    return Math.max(0, Math.min(100, score));
  }, [systemOnline, aiModelReady, networkQuality, maintenanceMode]);

  // Light mode variable overrides (scoped to this page)
  const lightVars: React.CSSProperties = lightMode
    ? {
        // background & surfaces
        // @ts-ignore CSS custom props
        "--color-background": "#f8fafc",
        "--color-foreground": "#0f172a",
        "--color-card": "#ffffff",
        "--color-card-foreground": "#0f172a",
        "--color-popover": "#ffffff",
        "--color-popover-foreground": "#0f172a",
        "--color-secondary": "#f1f5f9",
        "--color-secondary-foreground": "#0f172a",
        "--color-muted": "#eef2f7",
        "--color-muted-foreground": "#475569",
        "--color-border": "#e5e7eb",
        "--color-input": "#e5e7eb",
        // brand and accents
        "--color-primary": "#ff7a45",
        "--color-primary-foreground": "#111213",
        "--color-accent": "#6ee7b7",
        "--color-accent-foreground": "#0f172a",
        // states
        "--color-destructive": "#ef4444",
        "--color-destructive-foreground": "#ffffff",
        // charts
        "--color-chart-1": "#ff7a45",
        "--color-chart-2": "#fb923c",
        "--color-chart-3": "#f59e0b",
        "--color-chart-4": "#6ee7b7",
        "--color-chart-5": "#22c55e",
      }
    : {};

  return (
    <main className="min-h-dvh w-full bg-background text-foreground" style={lightVars}>
      {/* Top Navigation */}
      <header className="sticky top-0 z-40 w-full border-b border-[--color-border] bg-card/70 backdrop-blur">
        <div className="mx-auto max-w-7xl px-4 sm:px-6">
          <div className="flex h-14 items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <div className="size-6 rounded-md bg-[--color-primary]"></div>
                <span className="font-semibold">MineGuard</span>
              </div>
              <Separator orientation="vertical" className="mx-1 hidden h-6 bg-[--color-border] sm:block" />
              <div className="hidden items-center gap-2 sm:flex">
                <StatusPill
                  icon={Wifi}
                  label={networkQuality === "good" ? "Network: Good" : networkQuality === "degraded" ? "Network: Degraded" : "Network: Down"}
                  color={
                    networkQuality === "good"
                      ? "bg-[--color-success] text-black"
                      : networkQuality === "degraded"
                      ? "bg-[--color-chart-3] text-black"
                      : "bg-[--color-destructive] text-[--color-destructive-foreground]"
                  }
                />
                <StatusPill
                  icon={Cpu}
                  label={aiModelReady ? "AI Model: Ready" : "AI Model: Updating"}
                  color={
                    aiModelReady
                      ? "bg-[--color-success] text-black"
                      : "bg-[--color-chart-3] text-black"
                  }
                />
                <StatusPill
                  icon={ShieldAlert}
                  label={systemOnline ? "System: Online" : "System: Offline"}
                  color={
                    systemOnline
                      ? "bg-[--color-success] text-black"
                      : "bg-[--color-destructive] text-[--color-destructive-foreground]"
                  }
                />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Select value={selectedSite} onValueChange={setSelectedSite}>
                <SelectTrigger className="h-8 w-[160px] bg-secondary border-[--color-border]" aria-label="Select site">
                  <SelectValue placeholder="Select site" />
                </SelectTrigger>
                <SelectContent className="bg-popover text-popover-foreground border-[--color-border]">
                  {sites.map((s) => (
                    <SelectItem key={s.id} value={s.id}>
                      {s.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button variant="outline" className="hidden border-[--color-border] bg-secondary hover:bg-[--color-card] md:inline-flex" onClick={() => setMaintenanceMode((v) => !v)}>
                {maintenanceMode ? "Exit Maintenance" : "Maintenance"}
              </Button>
              <Button variant="outline" className="hidden border-[--color-border] bg-secondary hover:bg-[--color-card] md:inline-flex" onClick={() => setNotifyOps((v) => !v)}>
                <Bell className="mr-2 size-4" />
                {notifyOps ? "Notifications On" : "Notifications Off"}
              </Button>
              <Button variant="outline" className="border-[--color-border] bg-secondary hover:bg-[--color-card]" onClick={() => setLightMode((v) => !v)}>
                {lightMode ? "Dark" : "Light"}
              </Button>
              <Link href="/settings" className="inline-flex items-center">
                <Button variant="outline" className="border-[--color-border] bg-secondary hover:bg-[--color-card]">
                  <Settings className="size-4" />
                </Button>
              </Link>
              <div className="ml-1">
                <Avatar className="size-8">
                  <AvatarImage src="https://api.dicebear.com/7.x/identicon/svg?seed=mineguard" alt="User" />
                  <AvatarFallback>MG</AvatarFallback>
                </Avatar>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Summary */}
      <section className="mx-auto max-w-7xl px-4 py-6 sm:px-6">
        <div className="flex flex-col gap-4">
          <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
            <div>
              <h1 className="text-xl font-semibold sm:text-2xl">Mine Safety Overview</h1>
              <p className="text-sm text-muted-foreground">
                Site:{" "}
                <span className="font-medium">
                  {sites.find((s) => s.id === selectedSite)?.name}
                </span>{" "}
                • {siteSensors.length} sensors • {unresolvedAlerts} active alerts
              </p>
            </div>
            <div className="w-full sm:w-[360px]">
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>System Health</span>
                <span>{systemHealth}%</span>
              </div>
              <Progress
                value={systemHealth}
                className={cn(
                  "mt-2 h-2 bg-[--color-muted]",
                  systemHealth >= 70
                    ? "[&>div]:bg-[--color-success]"
                    : systemHealth >= 35
                    ? "[&>div]:bg-[--color-chart-3]"
                    : "[&>div]:bg-[--color-destructive]"
                )}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <Card className="rounded-lg border-[--color-border] bg-[--color-surface-2] p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Current Risk (baseline)</span>
                <Badge
                  className={cn(
                    "text-xs",
                    appRiskBaseline >= 70
                      ? "bg-[--color-destructive] text-[--color-destructive-foreground]"
                      : appRiskBaseline >= 35
                      ? "bg-[--color-chart-3] text-black"
                      : "bg-[--color-success] text-black"
                  )}
                >
                  {appRiskBaseline}%
                </Badge>
              </div>
              <p className="mt-2 text-2xl font-semibold">{riskLabel(appRiskBaseline)}</p>
              <div className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
                <span>Ops notifications</span>
                <Badge className={cn("text-[10px]", notifyOps ? "bg-[--color-success] text-black" : "bg-[--color-muted]")}>
                  {notifyOps ? "Enabled" : "Muted"}
                </Badge>
              </div>
            </Card>

            <Card className="rounded-lg border-[--color-border] bg-[--color-surface-2] p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Active Sensors</span>
                <Badge className="text-xs bg-[--color-chart-1] text-black">{siteSensors.length}</Badge>
              </div>
              <p className="mt-2 text-2xl font-semibold">Monitoring</p>
              <div className="mt-3 text-xs text-muted-foreground">Live data streaming enabled</div>
            </Card>

            <Card className="rounded-lg border-[--color-border] bg-[--color-surface-2] p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Recent Alerts</span>
                <Badge
                  className={cn(
                    "text-xs",
                    unresolvedAlerts > 0
                      ? "bg-[--color-destructive] text-[--color-destructive-foreground]"
                      : "bg-[--color-success] text-black"
                  )}
                >
                  {unresolvedAlerts}
                </Badge>
              </div>
              <p className="mt-2 text-2xl font-semibold">
                {unresolvedAlerts > 0 ? "Attention Needed" : "All Clear"}
              </p>
              <div className="mt-3 text-xs text-muted-foreground">
                {unresolvedAlerts > 0 ? "Review and acknowledge alerts below" : "No action required"}
              </div>
            </Card>
          </div>
        </div>
      </section>

      {/* 3D Simulation (iframe placeholder) */}
      <section className="mx-auto max-w-7xl px-4 pb-6 sm:px-6">
        <Card className="overflow-hidden rounded-lg border-[--color-border] bg-[--color-surface-2]">
          <div className="flex items-center justify-between border-b border-[--color-border] px-4 py-3">
            <h2 className="text-sm font-semibold">3D Simulation</h2>
            <Badge className="bg-[--color-chart-4] text-black">Placeholder</Badge>
          </div>
          <div className="relative">
            <iframe
              title="Mine 3D Simulation Placeholder"
              className="block h-[380px] w-full"
              srcDoc={`<!doctype html><html><head><meta charset=\"utf-8\"/><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"/><style>html,body{height:100%;margin:0;font-family:Inter,system-ui,sans-serif;background:#0b0d0f;color:#e6e7e8;display:grid;place-items:center} .card{border:1px solid #2a2d2f;border-radius:12px;padding:24px;max-width:780px;background:#131517} .muted{color:#9aa1a8}</style></head><body><div class=\"card\"><h3 style=\"margin:0 0 8px\">3D Simulation Placeholder</h3><p class=\"muted\" style=\"margin:0 0 12px\">Embed your Unity/WebGL build URL here. This iframe is ready.</p><code style=\"font-size:12px\">&lt;iframe src=&quot;https://your-hosted-build/index.html&quot; allow=&quot;fullscreen; xr-spatial-tracking; accelerometer; gyroscope;" /&gt;</code></div></body></html>`}
              allow="fullscreen; xr-spatial-tracking; accelerometer; gyroscope;"
            />
          </div>
        </Card>
      </section>

      {/* Warning Forecast */}
      <section className="mx-auto max-w-7xl px-4 pb-10 sm:px-6">
        <Card className="rounded-lg border-[--color-border] bg-[--color-surface-2] p-4">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold">Warning Forecast</h2>
            <span className="text-xs text-muted-foreground">Next 48 hours</span>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <div className="mb-1 flex items-center justify-between text-xs text-muted-foreground">
                <span>24 hours</span>
                <span>{Math.min(100, Math.round(appRiskBaseline * 1.25))}%</span>
              </div>
              <Progress
                value={Math.min(100, Math.round(appRiskBaseline * 1.2))}
                className={cn(
                  "h-2 bg-[--color-muted]",
                  appRiskBaseline >= 56 ? "[&>div]:bg-[--color-destructive]" : appRiskBaseline >= 28 ? "[&>div]:bg-[--color-chart-3]" : "[&>div]:bg-[--color-success]"
                )}
              />
            </div>
            <div>
              <div className="mb-1 flex items-center justify-between text-xs text-muted-foreground">
                <span>48 hours</span>
                <span>{Math.min(100, Math.round(appRiskBaseline * 1.6))}%</span>
              </div>
              <Progress
                value={Math.min(100, Math.round(appRiskBaseline * 1.6))}
                className={cn(
                  "h-2 bg-[--color-muted]",
                  appRiskBaseline >= 44 ? "[&>div]:bg-[--color-destructive]" : appRiskBaseline >= 22 ? "[&>div]:bg-[--color-chart-3]" : "[&>div]:bg-[--color-success]"
                )}
              />
            </div>
          </div>
        </Card>
      </section>

      {/* Integrated Dashboard */}
      <section className="mx-auto max-w-7xl px-4 pb-10 sm:px-6">
        <MineSafetyDashboard
          className="w-full"
          initialSensors={siteSensors}
          initialAlerts={seedAlerts}
          initialRisk={appRiskBaseline}
          vibrationLive={vibrationLive}
          displacementLive={displacementLive}
          hydroLive={hydroLive}
          environmentLive={environmentLive}
          riskLevelLive={riskLevelLive}
        />
        <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
          <Button
            variant="outline"
            className="border-[--color-border] bg-secondary hover:bg-[--color-card]"
            onClick={() => setSystemOnline((v) => !v)}
          >
            Toggle System {systemOnline ? "Offline" : "Online"}
          </Button>
          <Select
            value={networkQuality}
            onValueChange={(v) => setNetworkQuality(v as "good" | "degraded" | "down")}
          >
            <SelectTrigger className="bg-secondary border-[--color-border]">
              <SelectValue placeholder="Network" />
            </SelectTrigger>
            <SelectContent className="bg-popover text-popover-foreground border-[--color-border]">
              <SelectItem value="good">Network: Good</SelectItem>
              <SelectItem value="degraded">Network: Degraded</SelectItem>
              <SelectItem value="down">Network: Down</SelectItem>
            </SelectContent>
          </Select>
          <div className="flex items-center justify-between rounded-lg border border-[--color-border] bg-[--color-surface-2] px-3 py-2">
            <span className="text-sm">AI Model</span>
            <div className="flex items-center gap-2">
              <Badge className={cn("text-xs", aiModelReady ? "bg-[--color-success] text-black" : "bg-[--color-chart-3] text-black")}>
                {aiModelReady ? "Ready" : "Updating"}
              </Badge>
              <Button
                size="sm"
                className="bg-[--color-primary] text-[--color-primary-foreground] hover:opacity-90"
                onClick={() => setAiModelReady((v) => !v)}
              >
                {aiModelReady ? "Simulate Update" : "Set Ready"}
              </Button>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}

function StatusPill({
  icon: Icon,
  label,
  color,
}: {
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  label: string;
  color: string;
}) {
  return (
    <span className={cn("inline-flex items-center gap-1 rounded-md px-2 py-1 text-[10px] font-medium", color)}>
      <Icon className="size-3.5" aria-hidden />
      {label}
    </span>
  );
}

function computeRiskFromLive(
  vibration: { accelerometer?: number; geophone?: number; seismometer?: number } | null,
  displacement: { crack?: number } | null,
  environment: { rain?: number } | null
): "LOW" | "MEDIUM" | "HIGH" {
  const vib = Math.max(
    vibration?.accelerometer ?? 0,
    vibration?.geophone ?? 0,
    vibration?.seismometer ?? 0
  );
  const crack = displacement?.crack ?? 0;
  const rain = environment?.rain ?? 0;

  // Match backend risk calculation logic
  if ((vib > 1.5 || crack > 3) && rain > 50) return "HIGH";
  if (vib > 0.5 || crack > 1) return "MEDIUM";
  return "LOW";
}

function riskLabel(risk: number) {
  if (risk < 35) return "Safe";
  if (risk < 70) return "Warning";
  return "Danger";
}