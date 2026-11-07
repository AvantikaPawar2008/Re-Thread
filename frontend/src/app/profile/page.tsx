import type { Metadata } from "next";
import { ProfileView } from "@/components/auth/ProfileView";

export const metadata: Metadata = { title: "Your profile · RE-THREAD" };

export default function ProfilePage() {
  return <ProfileView />;
}