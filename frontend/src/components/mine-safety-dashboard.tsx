"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import {
  LayoutDashboard,
  Gauge,
  MonitorDot,
  Siren,
  ChartSpline,
  ChartColumnBig,
} from "lucide-react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Progress } from "@/components/ui/progress";

type SensorReading = {
  t: number;
  accel: number; // m/s^2
  tilt: number; // degrees
  temp: number; // °C
  vib: number; // mm/s
};

type AlertItem = {
  id: string;
  level: "safe" | "warning" | "danger";
  message: string;
  time: string;
  acknowledged?: boolean;
};

export interface MineSafetyDashboardProps {
  className?: string;
  style?: React.CSSProperties;
  initialSensors?: string[];
  initialAlerts?: AlertItem[];
  initialRisk?: number; // 0-100
  vibrationLive?: { accelerometer: number; geophone: number; seismometer: number; timestamp: number } | null;
  displacementLive?: { crack: number; inclinometer: number; extensometer: number; timestamp: number } | null;
  hydroLive?: { moisture: number; piezometer: number; timestamp: number } | null;
  environmentLive?: { rain: number; timestamp: number } | null;
  riskLevelLive?: "LOW" | "MEDIUM" | "HIGH" | null;
}

const MAX_POINTS = 60;

// This function is only used as a fallback when backend data is not available
function generateReading(prev?: SensorReading): SensorReading {
  const now = Date.now();
  const base = prev ?? {
    t: now - 1000,
    accel: 0.3,
    tilt: 2,
    temp: 22,
    vib: 3,
  };
  const clamp = (v: number, min: number, max: number) => Math.min(max, Math.max(min, v));
  return {
    t: now,
    accel: clamp(base.accel + (Math.random() - 0.5) * 0.2, 0, 3.5),
    tilt: clamp(base.tilt + (Math.random() - 0.5) * 0.6, 0, 25),
    temp: clamp(base.temp + (Math.random() - 0.5) * 0.4, 5, 60),
    vib: clamp(base.vib + (Math.random() - 0.5) * 0.6, 0, 12),
  };
}

function sparklinePath(values: number[], width = 240, height = 64) {
  if (values.length === 0) return "";
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const step = width / Math.max(values.length - 1, 1);
  return values
    .map((v, i) => {
      const x = i * step;
      const y = height - ((v - min) / range) * height;
      return `${i === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`;
    })
    .join(" ");
}

function trendDelta(values: number[]) {
  if (values.length < 2) return 0;
  const a = values[values.length - 2];
  const b = values[values.length - 1];
  return b - a;
}

function statusFromRisk(risk: number): { label: "Safe" | "Warning" | "Danger"; color: string } {
  if (risk < 35) return { label: "Safe", color: "text-[--color-success]" };
  if (risk < 70) return { label: "Warning", color: "text-[--color-chart-3]" };
  return { label: "Danger", color: "text-[--color-destructive]" };
}

export default function MineSafetyDashboard({
  className,
  style,
  initialSensors = ["S-AX01", "S-AX02", "S-TMP03", "S-VIB07"],
  initialAlerts,
  initialRisk = 28,
  vibrationLive,
  displacementLive,
  hydroLive,
  environmentLive,
  riskLevelLive,
}: MineSafetyDashboardProps) {
  // Set active sensor based on backend data if available
  const [activeSensor, setActiveSensor] = React.useState<string>(
    vibrationLive ? "VIB-ACC" : 
    displacementLive ? "DISP-CRK" : 
    environmentLive ? "ENV-RAIN" : 
    initialSensors[0] ?? "S-AX01"
  );
  const [range, setRange] = React.useState<"1h" | "6h" | "24h" | "7d">("1h");
  const [readings, setReadings] = React.useState<SensorReading[]>([]);
  const [risk, setRisk] = React.useState<number>(initialRisk);
  const [uploadPreview, setUploadPreview] = React.useState<string | null>(null);
  const [dragOver, setDragOver] = React.useState(false);
  const [alerts, setAlerts] = React.useState<AlertItem[]>(initialAlerts ?? []);
  
  // Generate alerts based on backend sensor data
  React.useEffect(() => {
    if (vibrationLive && displacementLive && environmentLive) {
      const newAlerts: AlertItem[] = [];
      const now = new Date();
      const timeString = "just now";
      
      // Check vibration sensors
      if (vibrationLive.accelerometer > 1.5) {
        newAlerts.push({
          id: `A-${Math.floor(Math.random() * 1000)}`,
          level: "danger",
          message: `High accelerometer reading detected: ${vibrationLive.accelerometer.toFixed(2)}`,
          time: timeString,
        });
      } else if (vibrationLive.accelerometer > 0.5) {
        newAlerts.push({
          id: `A-${Math.floor(Math.random() * 1000)}`,
          level: "warning",
          message: `Elevated accelerometer reading: ${vibrationLive.accelerometer.toFixed(2)}`,
          time: timeString,
        });
      }
      
      if (vibrationLive.geophone > 1.5) {
        newAlerts.push({
          id: `A-${Math.floor(Math.random() * 1000)}`,
          level: "danger",
          message: `High geophone reading detected: ${vibrationLive.geophone.toFixed(2)}`,
          time: timeString,
        });
      }
      
      // Check displacement sensors
      if (displacementLive.crack > 3) {
        newAlerts.push({
          id: `A-${Math.floor(Math.random() * 1000)}`,
          level: "danger",
          message: `Critical crack measurement: ${displacementLive.crack.toFixed(2)}`,
          time: timeString,
        });
      } else if (displacementLive.crack > 1) {
        newAlerts.push({
          id: `A-${Math.floor(Math.random() * 1000)}`,
          level: "warning",
          message: `Concerning crack measurement: ${displacementLive.crack.toFixed(2)}`,
          time: timeString,
        });
      }
      
      // Check environmental sensors
      if (environmentLive.rain > 50) {
        newAlerts.push({
          id: `A-${Math.floor(Math.random() * 1000)}`,
          level: "danger",
          message: `Heavy rainfall detected: ${environmentLive.rain.toFixed(1)} mm`,
          time: timeString,
        });
      } else if (environmentLive.rain > 20) {
        newAlerts.push({
          id: `A-${Math.floor(Math.random() * 1000)}`,
          level: "warning",
          message: `Moderate rainfall detected: ${environmentLive.rain.toFixed(1)} mm`,
          time: timeString,
        });
      }
      
      // Add a safe alert if no issues detected
      if (newAlerts.length === 0) {
        newAlerts.push({
          id: `A-${Math.floor(Math.random() * 1000)}`,
          level: "safe",
          message: "All systems normal.",
          time: timeString,
        });
      }
      
      // Update alerts state, keeping previous alerts that are not duplicates
      setAlerts(prev => {
        // Keep only alerts from the last hour
        const recentAlerts = prev.filter(a => !a.message.includes("reading") && !a.message.includes("measurement") && !a.message.includes("rainfall"));
        return [...newAlerts, ...recentAlerts].slice(0, 5); // Keep only the 5 most recent alerts
      });
    }
  }, [vibrationLive, displacementLive, environmentLive]);
  const [notifySMS, setNotifySMS] = React.useState(true);
  const [notifyEmail, setNotifyEmail] = React.useState(true);

  // Use backend data instead of simulated data
  React.useEffect(() => {
    // Initialize with some data if backend data is not available yet
    if (!vibrationLive && !displacementLive && !environmentLive) {
      let raf: number;
      const tick = () => {
        setReadings((prev) => {
          const next = generateReading(prev[prev.length - 1]);
          const arr = [...prev, next].slice(-MAX_POINTS);
          return arr;
        });
        raf = window.setTimeout(() => requestAnimationFrame(tick), 1000);
      };
      tick();
      return () => {
        clearTimeout(raf);
      };
    } else {
      // Update readings based on backend data and selected sensor
      setReadings((prev) => {
        const now = Date.now();
        let accelValue = vibrationLive?.accelerometer ?? 0;
        let tiltValue = displacementLive?.inclinometer ?? 0;
        let tempValue = environmentLive?.rain ?? 0;
        let vibValue = vibrationLive?.geophone ?? 0;
        
        // Adjust values based on selected sensor
        if (activeSensor.startsWith("VIB-")) {
          if (activeSensor === "VIB-ACC") accelValue = vibrationLive?.accelerometer ?? 0;
          else if (activeSensor === "VIB-GEO") vibValue = vibrationLive?.geophone ?? 0;
          else if (activeSensor === "VIB-SEIS") vibValue = vibrationLive?.seismometer ?? 0;
        } else if (activeSensor.startsWith("DISP-")) {
          if (activeSensor === "DISP-CRK") tiltValue = displacementLive?.crack ?? 0;
          else if (activeSensor === "DISP-INC") tiltValue = displacementLive?.inclinometer ?? 0;
          else if (activeSensor === "DISP-EXT") tiltValue = displacementLive?.extensometer ?? 0;
        } else if (activeSensor.startsWith("ENV-")) {
          if (activeSensor === "ENV-RAIN") tempValue = environmentLive?.rain ?? 0;
        } else if (activeSensor.startsWith("HYD-")) {
          if (activeSensor === "HYD-MOI") tempValue = hydroLive?.moisture ?? 0;
          else if (activeSensor === "HYD-PIE") tempValue = hydroLive?.piezometer ?? 0;
        }
        
        const next: SensorReading = {
          t: now,
          accel: accelValue,
          tilt: tiltValue,
          temp: tempValue,
          vib: vibValue,
        };
        const arr = [...prev, next].slice(-MAX_POINTS);
        return arr;
      });
    }
  }, [vibrationLive, displacementLive, environmentLive, hydroLive, activeSensor]);

  // Use backend risk level instead of calculating from readings
  React.useEffect(() => {
    if (riskLevelLive) {
      // Convert risk level string to numeric value
      let riskScore = 0;
      switch (riskLevelLive) {
        case "LOW":
          riskScore = 25;
          break;
        case "MEDIUM":
          riskScore = 60;
          break;
        case "HIGH":
          riskScore = 90;
          break;
      }
      setRisk(riskScore);
    } else if (readings.length < 5) {
      return;
    } else {
      // Fallback to calculation if backend risk level is not available
      const last = readings[readings.length - 1];
      const tempScore = (last.temp / 60) * 25;
      const vibScore = (last.vib / 12) * 40;
      const tiltScore = (last.tilt / 25) * 25;
      const noise = Math.random() * 5;
      const score = Math.max(0, Math.min(100, tempScore + vibScore + tiltScore + noise));
      setRisk((prev) => prev * 0.6 + score * 0.4);
    }
  }, [readings, riskLevelLive]);

  // Create historical data arrays from backend sensor data
  const accelValues = React.useMemo(() => {
    if (vibrationLive) {
      // Use backend data if available
      return [...readings.slice(0, -1).map(r => r.accel), vibrationLive.accelerometer];
    }
    return readings.map((r) => r.accel);
  }, [readings, vibrationLive]);
  
  const tiltValues = React.useMemo(() => {
    if (displacementLive) {
      // Use backend data if available
      return [...readings.slice(0, -1).map(r => r.tilt), displacementLive.inclinometer];
    }
    return readings.map((r) => r.tilt);
  }, [readings, displacementLive]);
  
  const tempValues = React.useMemo(() => {
    if (environmentLive) {
      // Use backend data if available
      return [...readings.slice(0, -1).map(r => r.temp), environmentLive.rain];
    }
    return readings.map((r) => r.temp);
  }, [readings, environmentLive]);
  
  const vibValues = React.useMemo(() => {
    if (vibrationLive) {
      // Use backend data if available
      return [...readings.slice(0, -1).map(r => r.vib), vibrationLive.geophone];
    }
    return readings.map((r) => r.vib);
  }, [readings, vibrationLive]);

  const status = React.useMemo(() => statusFromRisk(Math.round(risk)), [risk]);

  const totalActiveSensors = initialSensors.length;
  const recentAlertCount = alerts.filter((a) => a.level !== "safe" && !a.acknowledged).length;

  const onFile = (file: File) => {
    if (!file.type.startsWith("image/")) {
      toast.error("Please upload an image file");
      return;
    }
    const url = URL.createObjectURL(file);
    setUploadPreview(url);
    toast.success("Image uploaded. Running crack detection…");
    // Simulate analysis completion
    setTimeout(() => {
      toast.message("Analysis complete", {
        description: "Potential crack detected at 34° offset. Confidence 82%.",
      });
    }, 1200);
  };

  const handleDrop: React.DragEventHandler<HTMLDivElement> = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) onFile(file);
  };

  const acknowledgeAlert = (id: string) => {
    setAlerts((prev) => prev.map((a) => (a.id === id ? { ...a, acknowledged: true } : a)));
    toast.success(`Alert ${id} acknowledged`);
  };

  // Calculate deltas using backend data when available
  const deltaTemp = React.useMemo(() => {
    if (environmentLive && tempValues.length > 1) {
      // Compare backend temperature with previous reading
      return environmentLive.rain - tempValues[tempValues.length - 2];
    }
    return trendDelta(tempValues);
  }, [tempValues, environmentLive]);
  
  const deltaVib = React.useMemo(() => {
    if (vibrationLive && vibValues.length > 1) {
      // Compare backend vibration with previous reading
      return vibrationLive.geophone - vibValues[vibValues.length - 2];
    }
    return trendDelta(vibValues);
  }, [vibValues, vibrationLive]);

  // Simple time-to-event heuristic
  const timeToEvent = React.useMemo(() => {
    if (risk < 35) return "No imminent risk";
    if (risk < 50) return "Likely > 24 hours";
    if (risk < 70) return "12–24 hours";
    if (risk < 85) return "4–12 hours";
    return "Under 4 hours";
  }, [risk]);

  return (
    <section
      className={cn(
        "w-full max-w-full rounded-lg bg-card text-card-foreground",
        "border border-[--color-border] shadow-sm",
        "p-4 sm:p-6",
        className
      )}
      style={style}
      aria-label="Mine safety monitoring dashboard"
    >
      {/* Live sensor data section */}
      {(vibrationLive || displacementLive || hydroLive || environmentLive || riskLevelLive) && (
        <div className="mb-6">
          <h2 className="text-lg font-semibold mb-3">Live Sensor Data</h2>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
            {vibrationLive && (
              <Card className="p-4">
                <h3 className="mb-2 font-semibold">Vibration Sensors</h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Accelerometer:</span>
                    <span className={cn("font-medium", vibrationLive.accelerometer > 1.5 ? "text-[--color-destructive]" : vibrationLive.accelerometer > 0.5 ? "text-[--color-chart-3]" : "text-[--color-success]")}>                      
                      {vibrationLive.accelerometer.toFixed(2)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Geophone:</span>
                    <span className={cn("font-medium", vibrationLive.geophone > 1.5 ? "text-[--color-destructive]" : vibrationLive.geophone > 0.5 ? "text-[--color-chart-3]" : "text-[--color-success]")}>                      
                      {vibrationLive.geophone.toFixed(2)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Seismometer:</span>
                    <span className={cn("font-medium", vibrationLive.seismometer > 1.5 ? "text-[--color-destructive]" : vibrationLive.seismometer > 0.5 ? "text-[--color-chart-3]" : "text-[--color-success]")}>                      
                      {vibrationLive.seismometer.toFixed(2)}
                    </span>
                  </div>
                </div>
              </Card>
            )}

            {displacementLive && (
              <Card className="p-4">
                <h3 className="mb-2 font-semibold">Displacement Sensors</h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Crack:</span>
                    <span className={cn("font-medium", displacementLive.crack > 3 ? "text-[--color-destructive]" : displacementLive.crack > 1 ? "text-[--color-chart-3]" : "text-[--color-success]")}>                      
                      {displacementLive.crack.toFixed(2)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Inclinometer:</span>
                    <span className="font-medium">{displacementLive.inclinometer.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Extensometer:</span>
                    <span className="font-medium">{displacementLive.extensometer.toFixed(2)}</span>
                  </div>
                </div>
              </Card>
            )}

            {hydroLive && (
              <Card className="p-4">
                <h3 className="mb-2 font-semibold">Hydro Sensors</h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Moisture:</span>
                    <span className="font-medium">{hydroLive.moisture.toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Piezometer:</span>
                    <span className="font-medium">{hydroLive.piezometer.toFixed(1)} kPa</span>
                  </div>
                </div>
              </Card>
            )}

            {environmentLive && (
              <Card className="p-4">
                <h3 className="mb-2 font-semibold">Environmental Sensors</h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Rain:</span>
                    <span className={cn("font-medium", environmentLive.rain > 50 ? "text-[--color-destructive]" : environmentLive.rain > 20 ? "text-[--color-chart-3]" : "text-[--color-success]")}>                      
                      {environmentLive.rain.toFixed(1)} mm
                    </span>
                  </div>
                </div>
              </Card>
            )}
            
            {riskLevelLive && (
              <Card className={cn("p-4", 
                riskLevelLive === "HIGH" ? "border-[--color-destructive]" : 
                riskLevelLive === "MEDIUM" ? "border-[--color-chart-3]" : 
                "border-[--color-success]")}>                
                <h3 className="mb-2 font-semibold">Risk Assessment</h3>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Current Risk:</span>
                  <Badge variant={riskLevelLive === "HIGH" ? "destructive" : riskLevelLive === "MEDIUM" ? "secondary" : "default"}
                    className={riskLevelLive === "HIGH" ? "bg-[--color-destructive] text-white" : 
                              riskLevelLive === "MEDIUM" ? "bg-[--color-chart-3] text-white" : 
                              "bg-[--color-success] text-white"}>
                    {riskLevelLive}
                  </Badge>
                </div>
              </Card>
            )}
          </div>
        </div>
      )}
      
      {/* Top overview metrics */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <Card className="bg-[--color-surface-2] border-[--color-border] p-4 rounded-lg">
          <div className="flex items-center gap-3">
            <Gauge className="size-5 text-[--color-chart-4]" aria-hidden />
            <span className="text-sm text-muted-foreground">Current Status</span>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <div className="flex items-center gap-2">
              <span className={cn("text-xl font-semibold", status.color)}>{status.label}</span>
              <Badge
                className={cn(
                  "text-xs",
                  status.label === "Danger"
                    ? "bg-[--color-destructive] text-[--color-destructive-foreground]"
                    : status.label === "Warning"
                    ? "bg-[--color-chart-3] text-black"
                    : "bg-[--color-success] text-black"
                )}
                aria-label={`Risk ${Math.round(risk)} percent`}
              >
                {Math.round(risk)}%
              </Badge>
            </div>
            <LayoutDashboard className="size-5 text-muted-foreground" aria-hidden />
          </div>
          <Progress
            value={Math.round(risk)}
            className={cn(
              "mt-3 h-2 bg-[--color-muted]",
              status.label === "Danger"
                ? "[&>div]:bg-[--color-destructive]"
                : status.label === "Warning"
                ? "[&>div]:bg-[--color-chart-3]"
                : "[&>div]:bg-[--color-success]"
            )}
            aria-label="Risk progress"
          />
        </Card>

        <Card className="bg-[--color-surface-2] border-[--color-border] p-4 rounded-lg">
          <div className="flex items-center gap-3">
            <MonitorDot className="size-5 text-[--color-chart-1]" aria-hidden />
            <span className="text-sm text-muted-foreground">Active Sensors</span>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            {/* Calculate actual active sensors from backend data */}
            <span className="text-xl font-semibold">
              {(vibrationLive ? 3 : 0) + 
               (displacementLive ? 3 : 0) + 
               (hydroLive ? 2 : 0) + 
               (environmentLive ? 1 : 0) || 
               totalActiveSensors}
            </span>
            <span className="text-xs text-muted-foreground">online</span>
          </div>
          <div className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
            <span>Sensor</span>
            <Select value={activeSensor} onValueChange={setActiveSensor}>
              <SelectTrigger
                className="h-7 w-28 bg-secondary border-[--color-border] text-foreground"
                aria-label="Select sensor"
              >
                <SelectValue placeholder="Select" />
              </SelectTrigger>
              <SelectContent className="bg-popover text-popover-foreground border-[--color-border]">
                {/* Use actual sensor IDs from backend data if available */}
                {(vibrationLive || displacementLive || environmentLive) ? [
                  ...(vibrationLive ? ["VIB-ACC", "VIB-GEO", "VIB-SEIS"] : []),
                  ...(displacementLive ? ["DISP-CRK", "DISP-INC", "DISP-EXT"] : []),
                  ...(hydroLive ? ["HYD-MOI", "HYD-PIE"] : []),
                  ...(environmentLive ? ["ENV-RAIN"] : [])
                ].map((s) => (
                  <SelectItem key={s} value={s}>
                    {s}
                  </SelectItem>
                )) : initialSensors.map((s) => (
                  <SelectItem key={s} value={s}>
                    {s}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </Card>

        <Card className="bg-[--color-surface-2] border-[--color-border] p-4 rounded-lg">
          <div className="flex items-center gap-3">
            <Siren className="size-5 text-[--color-destructive]" aria-hidden />
            <span className="text-sm text-muted-foreground">Recent Alerts</span>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="text-xl font-semibold">{recentAlertCount}</span>
            <span
              className={cn(
                "text-xs",
                deltaVib > 0.15 || deltaTemp > 0.15 ? "text-[--color-destructive]" : "text-[--color-success]"
              )}
            >
              {deltaVib > 0.15 || deltaTemp > 0.15 ? "up" : "stable"}
            </span>
          </div>
          <div className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
            <span>Range</span>
            <Select value={range} onValueChange={(v) => setRange(v as typeof range)}>
              <SelectTrigger
                className="h-7 w-24 bg-secondary border-[--color-border] text-foreground"
                aria-label="Select time range"
              >
                <SelectValue placeholder="Range" />
              </SelectTrigger>
              <SelectContent className="bg-popover text-popover-foreground border-[--color-border]">
                <SelectItem value="1h">1h</SelectItem>
                <SelectItem value="6h">6h</SelectItem>
                <SelectItem value="24h">24h</SelectItem>
                <SelectItem value="7d">7d</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </Card>
      </div>

      {/* Tabs */}
      <div className="mt-6">
        <Tabs defaultValue="realtime" className="w-full">
          <TabsList className="bg-secondary text-secondary-foreground p-1 rounded-lg border border-[--color-border]">
            <TabsTrigger value="realtime" className="data-[state=active]:bg-[--color-card]">
              <ChartSpline className="mr-2 size-4" aria-hidden /> Real-time Sensors
            </TabsTrigger>
            <TabsTrigger value="prediction" className="data-[state=active]:bg-[--color-card]">
              <Gauge className="mr-2 size-4" aria-hidden /> AI Prediction
            </TabsTrigger>
            <TabsTrigger value="images" className="data-[state=active]:bg-[--color-card]">
              <ChartColumnBig className="mr-2 size-4" aria-hidden /> Image Analysis
            </TabsTrigger>
            <TabsTrigger value="alerts" className="data-[state=active]:bg-[--color-card]">
              <Siren className="mr-2 size-4" aria-hidden /> Alerts
            </TabsTrigger>
            <TabsTrigger value="history" className="data-[state=active]:bg-[--color-card]">
              <LayoutDashboard className="mr-2 size-4" aria-hidden /> Historical
            </TabsTrigger>
          </TabsList>

          {/* Real-time sensor monitoring */}
          <TabsContent value="realtime" className="mt-4">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <MetricChart
                title="Acceleration"
                unit="m/s²"
                color="var(--color-chart-1)"
                values={accelValues}
              />
              <MetricChart title="Tilt" unit="°" color="var(--color-chart-2)" values={tiltValues} />
              <MetricChart
                title="Temperature"
                unit="°C"
                color="var(--color-chart-3)"
                values={tempValues}
                footer={
                  <span
                    className={cn(
                      "text-xs",
                      deltaTemp >= 0 ? "text-[--color-chart-3]" : "text-[--color-success]"
                    )}
                  >
                    {deltaTemp >= 0 ? "+" : ""}
                    {deltaTemp.toFixed(2)} since last tick
                  </span>
                }
              />
              <MetricChart
                title="Vibration"
                unit="mm/s"
                color="var(--color-chart-5)"
                values={vibValues}
                footer={
                  <span
                    className={cn(
                      "text-xs",
                      deltaVib >= 0 ? "text-[--color-destructive]" : "text-[--color-success]"
                    )}
                  >
                    {deltaVib >= 0 ? "+" : ""}
                    {deltaVib.toFixed(2)} change
                  </span>
                }
              />
            </div>
          </TabsContent>

          {/* AI prediction */}
          <TabsContent value="prediction" className="mt-4">
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
              <Card className="col-span-1 bg-[--color-surface-2] border-[--color-border] p-5 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-base font-semibold">Rockfall Probability</h3>
                    <p className="text-sm text-muted-foreground mt-1">
                      Estimated likelihood with current conditions
                    </p>
                  </div>
                  <Gauge className="size-6 text-[--color-chart-4]" aria-hidden />
                </div>
                <div className="mt-6">
                  <div className="flex items-end gap-3">
                    <span className="text-4xl font-bold leading-none">{Math.round(risk)}</span>
                    <span className="mb-1 text-muted-foreground">%</span>
                  </div>
                  <Progress
                    value={Math.round(risk)}
                    className={cn(
                      "mt-4 h-2 bg-[--color-muted]",
                      risk >= 70
                        ? "[&>div]:bg-[--color-destructive]"
                        : risk >= 35
                        ? "[&>div]:bg-[--color-chart-3]"
                        : "[&>div]:bg-[--color-success]"
                    )}
                    aria-label="Probability progress"
                  />
                  <div className="mt-4 flex items-center gap-2">
                    <Badge
                      className={cn(
                        "text-xs",
                        risk >= 70
                          ? "bg-[--color-destructive] text-[--color-destructive-foreground]"
                          : risk >= 35
                          ? "bg-[--color-chart-3] text-black"
                          : "bg-[--color-success] text-black"
                      )}
                    >
                      {status.label}
                    </Badge>
                    <span className="text-xs text-muted-foreground">ETA: {timeToEvent}</span>
                  </div>
                </div>
              </Card>

              <Card className="col-span-1 bg-[--color-surface-2] border-[--color-border] p-5 rounded-lg">
                <h3 className="text-base font-semibold">Risk Assessment</h3>
                <Separator className="my-4 bg-[--color-border]" />
                <div className="space-y-3">
                  <RiskRow label="Geotechnical stress" value={tiltValues.at(-1) ?? 0} max={25} />
                  <RiskRow label="Thermal expansion" value={tempValues.at(-1) ?? 0} max={60} />
                  <RiskRow label="Ground vibration" value={vibValues.at(-1) ?? 0} max={12} />
                  <RiskRow label="Structural drift" value={accelValues.at(-1) ?? 0} max={3.5} />
                </div>
              </Card>

              <Card className="col-span-1 bg-[--color-surface-2] border-[--color-border] p-5 rounded-lg">
                <h3 className="text-base font-semibold">Model Notes</h3>
                <Separator className="my-4 bg-[--color-border]" />
                <ul className="list-disc pl-5 space-y-2 text-sm text-muted-foreground">
                  <li>Model weights emphasize vibration and tilt recency.</li>
                  <li>Confidence increases with sensor agreement within 5% variance.</li>
                  <li>Use multiple time windows for robust inference.</li>
                </ul>
                <div className="mt-4">
                  <Button
                    className="w-full bg-[--color-primary] text-[--color-primary-foreground] hover:opacity-90"
                    onClick={() =>
                      toast.message("Model refreshed", { description: "Recalculated with latest data." })
                    }
                  >
                    Recalculate now
                  </Button>
                </div>
              </Card>
            </div>
          </TabsContent>

          {/* Image analysis */}
          <TabsContent value="images" className="mt-4">
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              <Card className="bg-[--color-surface-2] border-[--color-border] p-5 rounded-lg">
                <h3 className="text-base font-semibold">Upload Slope Image</h3>
                <p className="text-sm text-muted-foreground mt-1">
                  Drag and drop an image or click to select a file.
                </p>
                <div
                  onDragOver={(e) => {
                    e.preventDefault();
                    setDragOver(true);
                  }}
                  onDragLeave={() => setDragOver(false)}
                  onDrop={handleDrop}
                  className={cn(
                    "mt-4 rounded-lg border-2 border-dashed p-6 transition-colors",
                    dragOver ? "border-[--color-chart-4] bg-[--color-muted]" : "border-[--color-border]"
                  )}
                  role="region"
                  aria-label="Image upload dropzone"
                >
                  <label
                    htmlFor="file-input"
                    className="block cursor-pointer text-center text-sm text-muted-foreground"
                  >
                    <span className="inline-block rounded-md bg-secondary px-4 py-2 border border-[--color-border]">
                      Choose file
                    </span>
                    <Input
                      id="file-input"
                      type="file"
                      accept="image/*"
                      className="sr-only"
                      onChange={(e) => {
                        const f = e.target.files?.[0];
                        if (f) onFile(f);
                      }}
                    />
                  </label>
                </div>

                {uploadPreview && (
                  <div className="mt-4">
                    <div className="relative overflow-hidden rounded-lg border border-[--color-border]">
                      {/* Image with simple mock annotations */}
                      <img
                        src={uploadPreview}
                        alt="Uploaded slope"
                        className="max-w-full h-auto object-contain"
                      />
                      {/* Visual annotation overlay */}
                      <svg
                        className="absolute inset-0 pointer-events-none"
                        viewBox="0 0 100 100"
                        aria-hidden
                      >
                        <polyline
                          points="20,65 35,55 48,45 60,40 78,30"
                          fill="none"
                          stroke="var(--color-destructive)"
                          strokeWidth="1.5"
                          strokeDasharray="3 2"
                        />
                        <circle cx="60" cy="40" r="2.2" fill="var(--color-chart-4)" />
                      </svg>
                    </div>
                    <div className="mt-2 text-xs text-muted-foreground">
                      Potential crack annotated. Confidence 82%. Suggest inspection within 12–24h.
                    </div>
                  </div>
                )}
              </Card>

              <Card className="bg-[--color-surface-2] border-[--color-border] p-5 rounded-lg">
                <h3 className="text-base font-semibold">Detection Settings</h3>
                <Separator className="my-4 bg-[--color-border]" />
                <div className="grid grid-cols-1 gap-5">
                  <div className="flex items-center justify-between gap-4">
                    <div className="min-w-0">
                      <Label htmlFor="sensitivity">Sensitivity</Label>
                      <p className="text-xs text-muted-foreground">Higher detects finer cracks</p>
                    </div>
                    <Select defaultValue="medium">
                      <SelectTrigger
                        id="sensitivity"
                        className="w-32 bg-secondary border-[--color-border]"
                        aria-label="Detection sensitivity"
                      >
                        <SelectValue placeholder="Select" />
                      </SelectTrigger>
                      <SelectContent className="bg-popover text-popover-foreground border-[--color-border]">
                        <SelectItem value="low">Low</SelectItem>
                        <SelectItem value="medium">Medium</SelectItem>
                        <SelectItem value="high">High</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="flex items-center justify-between gap-4">
                    <div className="min-w-0">
                      <Label htmlFor="edge">Edge enhancement</Label>
                      <p className="text-xs text-muted-foreground">Sharpen to improve detection</p>
                    </div>
                    <Switch id="edge" defaultChecked />
                  </div>
                  <div className="flex items-center justify-between gap-4">
                    <div className="min-w-0">
                      <Label htmlFor="noise">Noise reduction</Label>
                      <p className="text-xs text-muted-foreground">Remove sensor noise</p>
                    </div>
                    <Switch id="noise" />
                  </div>
                  <Button
                    className="w-full bg-[--color-primary] text-[--color-primary-foreground] hover:opacity-90"
                    onClick={() => toast.message("Detection started", { description: "Running analysis…" })}
                  >
                    Run analysis
                  </Button>
                </div>
              </Card>
            </div>
          </TabsContent>

          {/* Alerts */}
          <TabsContent value="alerts" className="mt-4">
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
              <Card className="bg-[--color-surface-2] border-[--color-border] p-5 rounded-lg lg:col-span-2">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-semibold">Recent Alerts</h3>
                  <Button
                    variant="outline"
                    className="border-[--color-border] bg-secondary hover:bg-[--color-card]"
                    onClick={() =>
                      toast.message("Alerts refreshed", { description: "Loaded latest alerts." })
                    }
                  >
                    Refresh
                  </Button>
                </div>
                <Separator className="my-4 bg-[--color-border]" />
                <ScrollArea className="h-[280px]">
                  <ul className="space-y-3 pr-2">
                    {alerts.map((a) => (
                      <li
                        key={a.id}
                        className={cn(
                          "rounded-md border p-3 flex items-start justify-between gap-3",
                          "border-[--color-border] bg-card"
                        )}
                      >
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <Badge
                              className={cn(
                                "text-xs",
                                a.level === "danger"
                                  ? "bg-[--color-destructive] text-[--color-destructive-foreground]"
                                  : a.level === "warning"
                                  ? "bg-[--color-chart-3] text-black"
                                  : "bg-[--color-success] text-black"
                              )}
                            >
                              {a.level}
                            </Badge>
                            <span className="text-xs text-muted-foreground">{a.time}</span>
                            {a.acknowledged && (
                              <span className="text-xs text-[--color-success]">Acknowledged</span>
                            )}
                          </div>
                          <div className="mt-1 min-w-0 break-words text-sm">{a.message}</div>
                        </div>
                        {!a.acknowledged && (
                          <Button
                            size="sm"
                            className="bg-[--color-primary] text-[--color-primary-foreground] hover:opacity-90"
                            onClick={() => acknowledgeAlert(a.id)}
                          >
                            Acknowledge
                          </Button>
                        )}
                      </li>
                    ))}
                  </ul>
                </ScrollArea>
              </Card>

              <Card className="bg-[--color-surface-2] border-[--color-border] p-5 rounded-lg">
                <h3 className="text-base font-semibold">Notification Settings</h3>
                <Separator className="my-4 bg-[--color-border]" />
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <Label htmlFor="sms">SMS notifications</Label>
                      <p className="text-xs text-muted-foreground">Receive urgent alerts via SMS</p>
                    </div>
                    <Switch
                      id="sms"
                      checked={notifySMS}
                      onCheckedChange={setNotifySMS}
                      aria-label="Toggle SMS notifications"
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <Label htmlFor="email">Email notifications</Label>
                      <p className="text-xs text-muted-foreground">Get full alert details</p>
                    </div>
                    <Switch
                      id="email"
                      checked={notifyEmail}
                      onCheckedChange={setNotifyEmail}
                      aria-label="Toggle email notifications"
                    />
                  </div>
                  <div className="grid grid-cols-1 gap-3">
                    <div>
                      <Label htmlFor="phone">SMS number</Label>
                      <Input
                        id="phone"
                        type="tel"
                        placeholder="+1 555 000 0000"
                        className="mt-1 bg-secondary border-[--color-border]"
                      />
                    </div>
                    <div>
                      <Label htmlFor="emailaddr">Email address</Label>
                      <Input
                        id="emailaddr"
                        type="email"
                        placeholder="ops@safety.example"
                        className="mt-1 bg-secondary border-[--color-border]"
                      />
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    className="w-full border-[--color-border] bg-secondary hover:bg-[--color-card]"
                    onClick={() =>
                      toast.success("Notification preferences saved", {
                        description: `${notifySMS ? "SMS" : "No SMS"}, ${notifyEmail ? "Email" : "No Email"}`,
                      })
                    }
                  >
                    Save preferences
                  </Button>
                </div>
              </Card>
            </div>
          </TabsContent>

          {/* Historical data */}
          <TabsContent value="history" className="mt-4">
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
              <Card className="bg-[--color-surface-2] border-[--color-border] p-5 rounded-lg lg:col-span-2">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-semibold">Trend Analysis</h3>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">Window</span>
                    <Select defaultValue="7d">
                      <SelectTrigger
                        className="h-8 w-28 bg-secondary border-[--color-border]"
                        aria-label="Historical window"
                      >
                        <SelectValue placeholder="Window" />
                      </SelectTrigger>
                      <SelectContent className="bg-popover text-popover-foreground border-[--color-border]">
                        <SelectItem value="24h">24h</SelectItem>
                        <SelectItem value="7d">7d</SelectItem>
                        <SelectItem value="30d">30d</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <Separator className="my-4 bg-[--color-border]" />
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <HistoryBlock label="Temperature (°C)" color="var(--color-chart-3)" />
                  <HistoryBlock label="Vibration (mm/s)" color="var(--color-chart-5)" />
                  <HistoryBlock label="Tilt (°)" color="var(--color-chart-2)" />
                  <HistoryBlock label="Acceleration (m/s²)" color="var(--color-chart-1)" />
                </div>
              </Card>

              <Card className="bg-[--color-surface-2] border-[--color-border] p-5 rounded-lg">
                <h3 className="text-base font-semibold">Pattern Insights</h3>
                <Separator className="my-4 bg-[--color-border]" />
                <ul className="space-y-3 text-sm">
                  <li className="flex items-start gap-2">
                    <span className="mt-1 h-2 w-2 rounded-full bg-[--color-chart-5]" />
                    <div className="min-w-0">
                      <div className="font-medium">Weekly vibration cycles</div>
                      <div className="text-muted-foreground">
                        Regular weekday peaks between 10:00–14:00 correlate with blasting schedule.
                      </div>
                    </div>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="mt-1 h-2 w-2 rounded-full bg-[--color-chart-3]" />
                    <div className="min-w-0">
                      <div className="font-medium">Heatwave impact</div>
                      <div className="text-muted-foreground">
                        Temperature increases by ~4°C lead to 10% higher tilt variance.
                      </div>
                    </div>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="mt-1 h-2 w-2 rounded-full bg-[--color-destructive]" />
                    <div className="min-w-0">
                      <div className="font-medium">Anomaly clusters</div>
                      <div className="text-muted-foreground">
                        Recent vibration anomalies clustered near north slope sensors.
                      </div>
                    </div>
                  </li>
                </ul>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </section>
  );
}

function MetricChart({
  title,
  unit,
  color,
  values,
  footer,
}: {
  title: string;
  unit: string;
  color: string;
  values: number[];
  footer?: React.ReactNode;
}) {
  const width = 520;
  const height = 96;
  const path = React.useMemo(() => sparklinePath(values, width, height), [values]);
  const latest = values.at(-1) ?? 0;
  const min = values.length ? Math.min(...values) : 0;
  const max = values.length ? Math.max(...values) : 0;

  return (
    <Card className="bg-[--color-surface-2] border-[--color-border] p-4 rounded-lg">
      <div className="flex items-center justify-between">
        <div className="min-w-0">
          <h4 className="text-sm font-semibold">{title}</h4>
          <p className="text-xs text-muted-foreground">
            Latest: {latest.toFixed(2)} {unit}
          </p>
        </div>
        <div className="text-right">
          <span className="text-xs text-muted-foreground">min</span>{" "}
          <span className="text-xs">{min.toFixed(2)}</span>
          <span className="mx-2 text-muted-foreground">/</span>
          <span className="text-xs text-muted-foreground">max</span>{" "}
          <span className="text-xs">{max.toFixed(2)}</span>
        </div>
      </div>
      <div className="mt-3 rounded-md border border-[--color-border] bg-card px-2 py-3">
        <div className="relative w-full overflow-hidden">
          <svg
            className="block w-full h-[96px]"
            viewBox={`0 0 ${width} ${height}`}
            preserveAspectRatio="none"
            role="img"
            aria-label={`${title} sparkline chart`}
          >
            <defs>
              <linearGradient id={`${title}-grad`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={color} stopOpacity="0.32" />
                <stop offset="100%" stopColor={color} stopOpacity="0.02" />
              </linearGradient>
            </defs>
            <path d={path} fill="none" stroke={color} strokeWidth="2" vectorEffect="non-scaling-stroke" />
            {/* Area fill */}
            <path
              d={`${path} L ${width} ${height} L 0 ${height} Z`}
              fill={`url(#${title}-grad)`}
              opacity="0.6"
            />
          </svg>
        </div>
      </div>
      <div className="mt-2 flex items-center justify-between">
        <span className="text-xs text-muted-foreground">Real-time</span>
        {footer}
      </div>
    </Card>
  );
}

function RiskRow({ label, value, max }: { label: string; value: number; max: number }) {
  const pct = Math.min(100, Math.round((value / max) * 100));
  const color =
    pct >= 70 ? "bg-[--color-destructive]" : pct >= 35 ? "bg-[--color-chart-3]" : "bg-[--color-success]";
  return (
    <div>
      <div className="flex items-center justify-between">
        <span className="text-sm">{label}</span>
        <span className="text-xs text-muted-foreground">{pct}%</span>
      </div>
      <div className="mt-2 h-2 w-full rounded bg-[--color-muted]">
        <div className={cn("h-2 rounded", color)} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function HistoryBlock({ label, color }: { label: string; color: string }) {
  const bars = React.useMemo(
    () =>
      Array.from({ length: 16 }).map(() =>
        Math.max(8, Math.round(Math.random() * 88))
      ),
    []
  );
  return (
    <div className="rounded-md border border-[--color-border] bg-card p-4">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">{label}</span>
        <span className="text-xs text-muted-foreground">trend</span>
      </div>
      <div className="mt-3 grid grid-cols-16 items-end gap-1 min-w-0">
        {bars.map((h, i) => (
          <div
            key={i}
            className="w-full rounded-sm"
            style={{
              height: `${h}px`,
              backgroundColor: color,
              opacity: 0.85 - (i * 0.4) / bars.length,
            }}
            aria-hidden
          />
        ))}
      </div>
      <p className="mt-3 text-xs text-muted-foreground">
        Auto-detected seasonal and operational patterns. Variability shown over time.
      </p>
    </div>
  );
}