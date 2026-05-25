import { AppShell } from "@/components/AppShell";
import { PartnersProvider } from "@/lib/partners-context";
import { RadarProvider } from "@/lib/state";

export default function HomePage() {
  return (
    <PartnersProvider>
      <RadarProvider>
        <AppShell />
      </RadarProvider>
    </PartnersProvider>
  );
}
