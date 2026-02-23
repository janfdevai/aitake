import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AITake | AI-Powered Orderbot & CRM for WhatsApp",
  description: "Automate your sales and customer support with AITake. A powerful Orderbot and CRM platform perfectly integrated with WhatsApp.",
  keywords: ["AITake", "AI Orderbot", "WhatsApp CRM", "Automated Sales", "Customer Support", "AI Assistant"],
  openGraph: {
    title: "AITake | Automate Sales on WhatsApp",
    description: "24/7 AI automated ordering and seamless CRM integration for your business.",
    type: "website",
  }
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
