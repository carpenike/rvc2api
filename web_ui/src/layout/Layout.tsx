import React from "react";
import type { ReactNode } from "react";
import Footer from "../components/Footer";
import Header from "../components/Header";

interface LayoutProps {
  children: ReactNode;
  wsStatus?: string;
}

const Layout: React.FC<LayoutProps> = ({ children, wsStatus }) => {
  return (
    <div className="flex flex-col min-h-screen bg-[var(--color-bg)] text-[var(--color-text)]">
      <Header wsStatus={wsStatus} />
      <main className="flex-1 flex flex-col min-h-0">{children}</main>
      <Footer />
    </div>
  );
};

export default Layout;
