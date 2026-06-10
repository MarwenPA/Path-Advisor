import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

import { QueryProvider } from "@/components/providers/query-provider";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Path-Advisor",
  description:
    "Continuous career-orientation platform for youth, from middle school through the first years of higher education.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr" className={`${inter.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col">
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  );
}
