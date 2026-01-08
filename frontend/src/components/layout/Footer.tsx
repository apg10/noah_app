// src/components/layout/Footer.tsx
import React from "react";

export const Footer: React.FC = () => {
  return (
    <footer className="bg-slate-900 text-white py-12 mt-12">
      <div className="layout-container">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div>
            <div className="flex items-center space-x-2 mb-4">
              <div className="w-8 h-8 bg-brand-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">N</span>
              </div>
              <span className="text-xl font-bold">Noah Food</span>
            </div>
            <p className="text-slate-400 font-normal">
              Dark Kitchen en Colombia. Comida fresca, rápida y confiable.
            </p>
          </div>

          <div>
            <h3 className="font-semibold mb-4">Enlaces Rápidos</h3>
            <ul className="space-y-2">
              <li>
                <button className="text-slate-400 hover:text-white font-normal">
                  Menú
                </button>
              </li>
              <li>
                <button className="text-slate-400 hover:text-white font-normal">
                  Seguimiento
                </button>
              </li>
              <li>
                <button className="text-slate-400 hover:text-white font-normal">
                  Ayuda
                </button>
              </li>
              <li>
                <button className="text-slate-400 hover:text-white font-normal">
                  Términos
                </button>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="font-semibold mb-4">Contacto</h3>
            <ul className="space-y-2 text-slate-400 font-normal">
              <li>📞 +57 300 123 4567</li>
              <li>✉️ hola@noahfood.co</li>
              <li>📍 Buga, Colombia</li>
            </ul>
          </div>

          <div>
            <h3 className="font-semibold mb-4">Horarios</h3>
            <ul className="space-y-2 text-slate-400 font-normal">
              <li>Lunes a Viernes: 11am - 10pm</li>
              <li>Sábados: 12pm - 11pm</li>
              <li>Domingos: 12pm - 9pm</li>
            </ul>
          </div>
        </div>

        <div className="border-t border-slate-800 mt-8 pt-8 text-center text-slate-400 font-normal">
          <p>© 2026 Noah Food. Todos los derechos reservados.</p>
        </div>
      </div>
    </footer>
  );
};
