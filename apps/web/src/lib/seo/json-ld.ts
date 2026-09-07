/**
 * JSON-LD serialization for `<script type="application/ld+json">` blocks.
 *
 * Epic 7 review fix (stored XSS): `JSON.stringify` does NOT escape `<`, so
 * admin-editable text (profession description, prospects_text, school
 * description, FAQ answers) containing `</script><script>...` would break
 * out of the JSON-LD block and execute — `dangerouslySetInnerHTML` does no
 * escaping by design. Replacing every `<` with its JSON unicode escape
 * (backslash-u003c) is enough: `<` is the only character that can
 * open/close a tag inside a `<script>` context, and the
 * escaped form is still strictly-equivalent JSON (parsers and Google's
 * structured-data crawler read it identically).
 *
 * Every JSON-LD `<script>` in the app MUST go through this helper — never
 * raw `JSON.stringify`.
 */
export function serializeJsonLd(value: unknown): string {
  return JSON.stringify(value).replace(/</g, "\\u003c");
}
