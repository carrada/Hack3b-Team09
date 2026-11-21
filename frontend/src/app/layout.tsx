import type { Metadata } from "next";
import { Poppins } from "next/font/google";
import { QueryProvider } from "@/components/providers/query-provider";
import "./globals.css";

const poppins = Poppins({
  variable: "--font-poppins",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Expedientes 3B",
  description:
    "Plataforma de revisión de expedientes con navegación ramificada y carga local de archivos.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="es" className={`${poppins.variable} h-full antialiased`}>
      <body className="min-h-full bg-background font-sans text-foreground flex flex-col">
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  );
}
