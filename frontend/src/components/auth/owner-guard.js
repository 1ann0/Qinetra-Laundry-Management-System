"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";

export default function OwnerGuard({ children }) {
  const router = useRouter();
  const { role } = useAuth();

  useEffect(() => {
    if (role && role !== "owner") {
      router.replace("/workspace");
    }
  }, [role, router]);

  if (role !== "owner") {
    return (
      <div className="loading-card" role="status">
        Checking owner access…
      </div>
    );
  }

  return children;
}
