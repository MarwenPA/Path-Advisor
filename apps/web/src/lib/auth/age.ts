/**
 * Age helpers for the signup flow (Story 1.4).
 *
 * Pure functions, no dependency on `date-fns` or other date libraries —
 * teen birth-date inputs always come in as `yyyy-MM-dd` strings from the
 * HTML date picker, so the manual diff is both simpler and faster.
 */

/**
 * Compute age in completed years for a `yyyy-MM-dd` birth date string.
 * Returns `null` when the input is missing, malformed, or in the future.
 */
export function ageInYears(
  birthDate: string | null | undefined,
  today: Date = new Date(),
): number | null {
  if (!birthDate || !/^\d{4}-\d{2}-\d{2}$/.test(birthDate)) return null;
  const [y, m, d] = birthDate.split("-").map(Number);
  if (!y || !m || !d) return null;
  // Story 1.4 review §P23: JavaScript's Date constructor silently rolls over
  // out-of-range month/day values (`new Date(2012, 12, 1)` → Jan 2013). Validate
  // the input ranges explicitly so an autofilled or programmatic invalid date
  // returns null rather than misclassifying the user's age.
  if (m < 1 || m > 12 || d < 1 || d > 31) return null;
  // Build the birth date at midnight in the user's local timezone so the
  // crossover happens on the actual birthday, not 24h before in UTC.
  const birth = new Date(y, m - 1, d);
  // After construction, verify the round-trip — catches Feb 30, etc.
  if (
    Number.isNaN(birth.getTime()) ||
    birth.getFullYear() !== y ||
    birth.getMonth() !== m - 1 ||
    birth.getDate() !== d
  )
    return null;
  if (birth > today) return null;
  let age = today.getFullYear() - birth.getFullYear();
  const hasHadBirthdayThisYear =
    today.getMonth() > birth.getMonth() ||
    (today.getMonth() === birth.getMonth() && today.getDate() >= birth.getDate());
  if (!hasHadBirthdayThisYear) age -= 1;
  return age;
}

/** True iff the user is strictly under `threshold` years old at `today`. */
export function isUnderAge(
  birthDate: string | null | undefined,
  threshold: number = 15,
  today: Date = new Date(),
): boolean {
  const age = ageInYears(birthDate, today);
  return age !== null && age < threshold;
}
