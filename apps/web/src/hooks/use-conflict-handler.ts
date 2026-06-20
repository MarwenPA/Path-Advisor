import { useState } from "react";

export type ConflictResolution = "reload" | "overwrite" | "cancel";

export interface ConflictState<T = unknown> {
  hasConflict: boolean;
  serverState: T | null;
  handle409: (serverState: T) => void;
  resolve: (resolution: ConflictResolution) => void;
}

export function useConflictHandler<T = unknown>(): ConflictState<T> {
  const [serverState, setServerState] = useState<T | null>(null);

  function handle409(state: T) {
    setServerState(state);
  }

  function resolve(_resolution: ConflictResolution) {
    setServerState(null);
  }

  return {
    hasConflict: serverState !== null,
    serverState,
    handle409,
    resolve,
  };
}
