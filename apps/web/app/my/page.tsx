"use client";
import Shell from "@/components/Shell";
import PersonalWorkspace from "@/components/PersonalWorkspace";
export default function MyPage() {
  return (
    <Shell
      title="My workspace"
      subtitle="Your personal profile, reports and targets."
    >
      <PersonalWorkspace />
    </Shell>
  );
}
