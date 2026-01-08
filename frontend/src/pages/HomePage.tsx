// src/pages/HomePage.tsx
import React from "react";

export const HomePage: React.FC = () => {
  return (
    <>
      {/* Hero */}
      <section className="bg-gradient-to-r from-brand-50 to-accent-50 py-12 md:py-20">
        <div className="layout-container">
          <div className="text-center">
            <h1 className="mb-4">Comida Fresca, Rápida y Confiable</h1>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto mb-8 font-normal">
              Dark Kitchen en Colombia. Pedidos online con entrega a domicilio.
              Calidad garantizada, siempre fresca.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button className="btn-primary">Ver Menú Completo</button>
              <button className="btn-secondary">Seguir Pedido</button>
            </div>
          </div>
        </div>
      </section>

      {/* Main content */}
      <section className="py-12">
        <div className="layout-container space-y-12">
          {/* Categorías populares */}
          <div>
            <h2 className="mb-6">Categorías Populares</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { icon: "🍔", label: "Hamburguesas" },
                { icon: "🍕", label: "Pizzas" },
                { icon: "🥗", label: "Ensaladas" },
                { icon: "🍹", label: "Bebidas" },
              ].map((cat) => (
                <div
                  key={cat.label}
                  className="card text-center hover:shadow-lg transition-shadow cursor-pointer"
                >
                  <div className="w-16 h-16 bg-brand-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <span className="text-2xl">{cat.icon}</span>
                  </div>
                  <h3 className="font-semibold">{cat.label}</h3>
                </div>
              ))}
            </div>
          </div>

          {/* Cómo funciona */}
          <div className="card p-8">
            <h2 className="text-center mb-8">¿Cómo Funciona?</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="text-center">
                <div className="w-12 h-12 bg-brand-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-xl">📱</span>
                </div>
                <h3 className="mb-2">1. Haz tu Pedido</h3>
                <p className="text-slate-600 font-normal">
                  Selecciona tus platillos favoritos desde nuestro menú online.
                </p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-accent-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-xl">👨‍🍳</span>
                </div>
                <h3 className="mb-2">2. Preparamos tu Comida</h3>
                <p className="text-slate-600 font-normal">
                  Nuestros chefs preparan cada pedido con ingredientes frescos.
                </p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-brand-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-xl">🚚</span>
                </div>
                <h3 className="mb-2">3. Entrega Rápida</h3>
                <p className="text-slate-600 font-normal">
                  Recibe tu pedido caliente y listo para disfrutar en minutos.
                </p>
              </div>
            </div>
          </div>

          {/* Estados de pedido (badges demo) */}
          <div className="card">
            <h2 className="mb-6">Estados de Pedido</h2>
            <div className="flex flex-wrap gap-4">
              <span className="badge badge-pending">PENDING</span>
              <span className="badge badge-progress">IN_PROGRESS</span>
              <span className="badge badge-ready">READY</span>
              <span className="badge badge-completed">COMPLETED</span>
              <span className="badge badge-cancelled">CANCELLED</span>
            </div>
            <p className="text-slate-600 mt-4 font-normal">
              Estos badges muestran el estado actual de cada pedido en nuestro
              sistema.
            </p>
          </div>
        </div>
      </section>
    </>
  );
};
