/**
 * `/ecole` — Story 5.6. Redirects to the reception queue, the only thing
 * this space does today. A real dashboard (Story 5.10 reporting) can
 * replace this later without touching `/ecole/outreach` itself.
 */
import { redirect } from "next/navigation";

export default function EcoleHomePage() {
  redirect("/ecole/outreach");
}
