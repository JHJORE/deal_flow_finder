import { AppShell } from "@/components/AppShell";
import { RadarProvider } from "@/lib/state";

export default function HomePage() {
  return (
    <RadarProvider>
      <AppShell />
    </RadarProvider>
  );
}
