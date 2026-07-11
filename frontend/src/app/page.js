"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/auth-context";

export default function Home() {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading) {
      router.replace(isAuthenticated ? "/workspace" : "/login");
    }
  }, [isAuthenticated, isLoading, router]);

  return (
    <main className="centered-page">
      <div className="loading-card" role="status">
        Opening QLMS…
      </div>
    </main>
  );
}
