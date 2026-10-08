import "./globals.css";
import type { Metadata } from "next";
import { Inter } from "next/font/google";

import { ThemeProvider } from "@/components/ThemeProvider";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

export const metadata: Metadata = {
  title: "MetroFlowNet · Apple Glass Transit Intelligence",
  description: "Apple Glassmorphism UI SaaS for AI-Powered Origin-Destination Passenger Flow Prediction and Smart Indian Metro Operations.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} relative min-h-screen antialiased`}>
        {/* Ambient Apple Glass Mesh Lights (Refracted through frosted panels) */}
        <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden" aria-hidden="true">
          <div className="absolute -top-[20%] -left-[10%] h-[600px] w-[600px] rounded-full bg-gradient-to-br from-blue-500/20 via-sky-400/15 to-transparent blur-[120px] dark:from-blue-600/25 dark:via-cyan-500/15" />
          <div className="absolute top-[10%] -right-[15%] h-[650px] w-[650px] rounded-full bg-gradient-to-bl from-purple-500/20 via-indigo-500/15 to-transparent blur-[130px] dark:from-purple-600/25 dark:via-indigo-600/15" />
          <div className="absolute bottom-[5%] left-[20%] h-[550px] w-[550px] rounded-full bg-gradient-to-tr from-cyan-400/15 via-teal-500/10 to-transparent blur-[110px] dark:from-cyan-500/15 dark:via-teal-600/10" />
        </div>

        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}
