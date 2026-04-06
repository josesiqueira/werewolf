import type { Metadata } from "next";
import "./globals.css";
import Navigation from "@/components/layout/Navigation";
import QueryProvider from "@/lib/query-provider";

export const metadata: Metadata = {
  title: "Werewolf AI Agents",
  description:
    "Research observation tool for AI agents playing social deduction",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-bg-void text-text-primary font-body antialiased">
        <QueryProvider>
          <div className="relative min-h-screen">
            {/* Main content area */}
            <main className="mx-auto max-w-content px-6 pt-8 pb-28 max-md:px-3 max-md:pt-4 max-md:pb-20">
              {children}
            </main>

            {/* Bottom navigation dock */}
            <Navigation />
          </div>
        </QueryProvider>
      </body>
    </html>
  );
}
