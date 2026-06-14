import { redirect } from "next/navigation";

export default function InternalAdminIndex() {
  redirect("/internal-admin/workspaces");
}
