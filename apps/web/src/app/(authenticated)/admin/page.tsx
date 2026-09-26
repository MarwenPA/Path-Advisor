import { redirect } from "next/navigation";

/** Back-office root — Métiers is the first shipped section (Story 9.1). */
export default function AdminIndexPage() {
  redirect("/admin/metiers");
}
