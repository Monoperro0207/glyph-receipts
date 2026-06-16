import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Glyph Receipts — Independent Verifier",
  description: "Verify signed, hash-chained agent spend receipts. Trust nobody; check the math.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
