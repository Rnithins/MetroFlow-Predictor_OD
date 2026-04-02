import "./globals.css";
import type { Metadata } from "next";
import { Manrope } from "next/font/google";

import { ThemeProvider } from "@/components/ThemeProvider";

const manrope = Manrope({
  subsets: ["latin"],
  variable: "--font-sans"
});

export const metadata: Metadata = {
  title: "MetroFlow Predictor",
  description: "AI-assisted metro passenger flow forecasting and analytics dashboard."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={manrope.variable}>
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}
