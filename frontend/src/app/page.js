"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";

export default function Home() {
  const router = useRouter();
  const { isAuthenticated, isLoading, role } = useAuth();

  useEffect(() => {
    if (!isLoading) {
      const signedInPath = role === "owner" ? "/finance" : "/workspace";
      router.replace(isAuthenticated ? signedInPath : "/login");
    }
  }, [isAuthenticated, isLoading, role, router]);

  return (
    <main className="centered-page">
      <div className="loading-card" role="status">
        Opening QLMS…
      </div>
    </main>
  );
}
