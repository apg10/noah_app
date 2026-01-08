import { Outlet } from "react-router-dom";
import { Navbar } from "./Navbar";
import { Footer } from "./Footer";
import { LayoutContainer } from "./LayoutContainer";

export default function Layout() {
  return (
    <div className="min-h-screen flex flex-col bg-white">
      <Navbar />

      <main className="flex-1">
        <LayoutContainer>
          <Outlet />
        </LayoutContainer>
      </main>

      <Footer />
    </div>
  );
}
