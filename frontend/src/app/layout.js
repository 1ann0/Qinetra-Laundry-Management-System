import { AuthProvider } from "@/context/auth-context";
import RequestStatus from "@/components/layout/request-status";
import "./globals.css";

export const metadata = {
  title: "QLMS | Qinetra Laundry",
  description: "Staff order tracking for Qinetra Laundry",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full">
        <AuthProvider><RequestStatus />{children}</AuthProvider>
      </body>
    </html>
  );
}
