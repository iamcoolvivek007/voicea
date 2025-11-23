import "@livekit/components-styles";
import { Metadata } from "next";
import { Public_Sans } from "next/font/google";
import "./globals.css";

const publicSans400 = Public_Sans({
  weight: "400",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Voice Assistant",
};

/**
 * RootLayout is the main layout component that wraps the entire application.
 * It sets up the HTML structure, applies the global font, and includes the body.
 *
 * @param {Object} props - The properties for the component.
 * @param {React.ReactNode} props.children - The child components to be rendered within the layout.
 * @returns {JSX.Element} The rendered root HTML structure.
 */
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`h-full ${publicSans400.className}`}>
      <body className="h-full">{children}</body>
    </html>
  );
}
