import React from "react";
import { Link, NavLink } from "react-router-dom";

interface NavbarProps {
  onOpenCart?: () => void;
  cartCount?: number;
}

export const Navbar: React.FC<NavbarProps> = ({ onOpenCart, cartCount = 0 }) => {
  const [mobileOpen, setMobileOpen] = React.useState(false);

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `text-slate-700 hover:text-brand-600 font-medium transition ${
      isActive ? "text-brand-600" : ""
    }`;

  const closeMobile = () => setMobileOpen(false);

  return (
    <header className="bg-white shadow-sm sticky top-0 z-50">
      <div className="layout-container">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2" onClick={closeMobile}>
            <div className="w-8 h-8 bg-brand-500 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-lg">N</span>
            </div>
            <span className="text-xl font-bold text-slate-800">Noah Food</span>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-8">
            <NavLink to="/menu" className={navLinkClass}>
              Menú
            </NavLink>
            <NavLink to="/tracking" className={navLinkClass}>
              Seguimiento
            </NavLink>
            <NavLink to="/help" className={navLinkClass}>
              Ayuda
            </NavLink>
            <NavLink to="/login" className={navLinkClass}>
              Iniciar Sesión
            </NavLink>
          </nav>

          {/* Right side */}
          <div className="flex items-center space-x-3">
            {/* Cart */}
            <button
              type="button"
              className="relative p-2 text-slate-700 hover:text-brand-600 transition"
              onClick={() => onOpenCart?.()}
              aria-label="Abrir carrito"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"
                />
              </svg>

              {cartCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-accent-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center font-medium">
                  {cartCount}
                </span>
              )}
            </button>

            {/* Mobile menu button */}
            <button
              type="button"
              className="md:hidden p-2 text-slate-700 hover:text-brand-600 transition"
              onClick={() => setMobileOpen((prev) => !prev)}
              aria-label="Abrir menú"
              aria-expanded={mobileOpen}
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        {mobileOpen && (
          <div className="md:hidden border-t border-slate-200">
            <nav className="py-4 space-y-2">
              <NavLink
                to="/menu"
                onClick={closeMobile}
                className="block py-2 text-slate-700 hover:text-brand-600 font-medium"
              >
                Menú
              </NavLink>

              <NavLink
                to="/tracking"
                onClick={closeMobile}
                className="block py-2 text-slate-700 hover:text-brand-600 font-medium"
              >
                Seguimiento
              </NavLink>

              <NavLink
                to="/help"
                onClick={closeMobile}
                className="block py-2 text-slate-700 hover:text-brand-600 font-medium"
              >
                Ayuda
              </NavLink>

              <NavLink
                to="/login"
                onClick={closeMobile}
                className="block py-2 text-slate-700 hover:text-brand-600 font-medium"
              >
                Iniciar Sesión
              </NavLink>
            </nav>
          </div>
        )}
      </div>
    </header>
  );
};
