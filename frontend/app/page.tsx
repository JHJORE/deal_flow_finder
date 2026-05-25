import { AppShell } from "@/components/AppShell";
import { DataProvider } from "@/lib/data-context";
import { RadarProvider } from "@/lib/state";

export default function HomePage() {
  return (
    <DataProvider>
      <RadarProvider>
        <AppShell />
      </RadarProvider>
    </DataProvider>
  );
}
