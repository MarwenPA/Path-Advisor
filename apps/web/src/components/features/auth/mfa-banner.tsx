"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { type CurrentUser, fetchCurrentUser } from "@/lib/api/auth";

/**
 * MfaBanner — Story 1.6 §AC8 (code-review D6).
 *
 * Layout-wide banner that surfaces on every authenticated page if the user
 * MUST enroll MFA (staff role) but hasn't done so yet. The banner is a
 * persistent reminder — staff users who never visit
 * `/parametres/securite/mfa` would otherwise miss the obligation.
 *
 * Client-rendered (mirrors LimitedModeBanner from Story 1.4): fetches
 * `/auth/user/` once on mount, hides for non-staff or already-enrolled
 * users so unaffected accounts see the layout exactly as pre-1.6.
 *
 * Visual treatment: red border + warning copy. The banner cannot be
 * dismissed — staff stay in front of the requirement until they enroll.
 */
export function MfaBanner() {
  const [user, setUser] = useState<CurrentUser | null>(null);

  useEffect(() => {
    fetchCurrentUser()
      .then(setUser)
      .catch(() => setUser(null));
  }, []);

  if (!user || !user.mfa_required_by_role || user.mfa_enrolled) {
    return null;
  }

  return (
    <div
      role="alert"
      className="border-l-4 border-text-error bg-red-50 px-4 py-3 text-sm"
    >
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-4 gap-y-2">
        <strong className="text-text-error">
          Double authentification obligatoire
        </strong>
        <span className="text-text">
          Ton rôle staff impose la MFA. Active-la maintenant pour sécuriser
          ton compte conformément à notre politique.
        </span>
        <Link
          href="/parametres/securite/mfa"
          className="ml-auto rounded border border-text-error px-3 py-1 font-medium text-text-error hover:bg-text-error hover:text-white"
        >
          Activer la MFA
        </Link>
      </div>
    </div>
  );
}
