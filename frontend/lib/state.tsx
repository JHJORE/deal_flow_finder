"use client";

import { createContext, useCallback, useContext, useMemo, useState } from "react";
import type { FirmId, OpenEntity, ViewId } from "./types";

type FeedFilter = "all" | "1" | "2" | "3" | "4";
type GraphMode = "theme" | "follow";
type PredWindow = "all" | "90";
type PeopleTab = "partners" | "founders";

type RadarState = {
  view: ViewId;
  setView: (v: ViewId) => void;
  open: OpenEntity;
  setOpen: (o: OpenEntity) => void;

  activeFirms: Set<FirmId>;
  toggleFirm: (id: FirmId) => void;

  feedFilter: FeedFilter;
  setFeedFilter: (f: FeedFilter) => void;

  archived: Set<string>;
  archiveSignal: (id: string) => void;
  unarchiveAll: () => void;

  watchlist: Set<string>;
  isWatched: (id: string) => boolean;
  toggleWatch: (id: string) => void;

  graphMode: GraphMode;
  setGraphMode: (m: GraphMode) => void;

  predWindow: PredWindow;
  setPredWindow: (w: PredWindow) => void;

  selectedTheme: string;
  setSelectedTheme: (k: string) => void;

  peopleTab: PeopleTab;
  setPeopleTab: (t: PeopleTab) => void;

  briefingDismissed: boolean;
  dismissBriefing: () => void;
};

const RadarCtx = createContext<RadarState | null>(null);

export function RadarProvider({ children }: { children: React.ReactNode }) {
  const [view, setViewState] = useState<ViewId>("signals");
  const [open, setOpen] = useState<OpenEntity>(null);
  const [activeFirms, setActiveFirms] = useState<Set<FirmId>>(
    new Set(["sequoia", "a16z", "yc"] as FirmId[])
  );
  const [feedFilter, setFeedFilter] = useState<FeedFilter>("all");
  const [archived, setArchived] = useState<Set<string>>(new Set());
  const [watchlist, setWatchlist] = useState<Set<string>>(new Set());
  const [graphMode, setGraphMode] = useState<GraphMode>("theme");
  const [predWindow, setPredWindow] = useState<PredWindow>("all");
  const [selectedTheme, setSelectedTheme] = useState<string>("agents");
  const [peopleTab, setPeopleTab] = useState<PeopleTab>("partners");
  const [briefingDismissed, setBriefingDismissed] = useState(false);

  const setView = useCallback((v: ViewId) => {
    setOpen(null);
    setViewState(v);
    if (typeof window !== "undefined") window.scrollTo({ top: 0, behavior: "smooth" });
  }, []);

  const toggleFirm = useCallback((id: FirmId) => {
    setActiveFirms((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      if (next.size === 0) next.add(id);
      return next;
    });
  }, []);

  const archiveSignal = useCallback((id: string) => {
    setArchived((prev) => {
      const n = new Set(prev);
      n.add(id);
      return n;
    });
  }, []);

  const unarchiveAll = useCallback(() => setArchived(new Set()), []);

  const isWatched = useCallback((id: string) => watchlist.has(id), [watchlist]);

  const toggleWatch = useCallback((id: string) => {
    setWatchlist((prev) => {
      const n = new Set(prev);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });
  }, []);

  const dismissBriefing = useCallback(() => setBriefingDismissed(true), []);

  const value = useMemo(
    () => ({
      view, setView,
      open, setOpen,
      activeFirms, toggleFirm,
      feedFilter, setFeedFilter,
      archived, archiveSignal, unarchiveAll,
      watchlist, isWatched, toggleWatch,
      graphMode, setGraphMode,
      predWindow, setPredWindow,
      selectedTheme, setSelectedTheme,
      peopleTab, setPeopleTab,
      briefingDismissed, dismissBriefing,
    }),
    [
      view, setView, open, activeFirms, toggleFirm, feedFilter, archived,
      archiveSignal, unarchiveAll, watchlist, isWatched, toggleWatch,
      graphMode, predWindow, selectedTheme, peopleTab, briefingDismissed, dismissBriefing,
    ]
  );

  return <RadarCtx.Provider value={value}>{children}</RadarCtx.Provider>;
}

export function useRadar() {
  const v = useContext(RadarCtx);
  if (!v) throw new Error("useRadar must be used inside <RadarProvider>");
  return v;
}
