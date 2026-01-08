import React from "react";
import { Link } from "react-router-dom";
import { useCartStore } from "../../store/cartStore";
import { formatCOP } from "../../utils/money";

type Props = {
  open: boolean;
  onClose: () => void;
};

export default function CartDrawer({ open, onClose }: Props) {
  const items = useCartStore((s) => s.items);
  const subtotal = useCartStore((s) => s.subtotal());
  const increase = useCartStore((s) => s.increase);
  const decrease = useCartStore((s) => s.decrease);
  const remove = useCartStore((s) => s.remove);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[60]">
      {/* overlay */}
      <button
        className="absolute inset-0 bg-black/40"
        onClick={onClose}
        aria-label="Cerrar carrito"
      />

      {/* panel */}
      <div className="absolute right-0 top-0 h-full w-full sm:w-[420px] bg-white shadow-xl flex flex-col">
        <div className="p-4 border-b flex items-center justify-between">
          <h2 className="font-semibold text-gray-900">Tu carrito</h2>
          <button
            onClick={onClose}
            className="w-9 h-9 rounded-lg hover:bg-gray-50"
            aria-label="Cerrar"
          >
            ✕
          </button>
        </div>

        <div className="p-4 flex-1 overflow-auto">
          {items.length === 0 ? (
            <p className="text-gray-600">Tu carrito está vacío.</p>
          ) : (
            <ul className="space-y-3">
              {items.map((i) => (
                <li
                  key={i.menu_item_id}
                  className="border rounded-xl p-3 flex items-start justify-between gap-3"
                >
                  <div>
                    <p className="font-medium text-gray-900">{i.name}</p>
                    <p className="text-sm text-gray-600">
                      {formatCOP(i.unit_price_cop)} c/u
                    </p>

                    <div className="mt-2 flex items-center gap-2">
                      <button
                        onClick={() => decrease(i.menu_item_id)}
                        className="w-8 h-8 rounded-lg border hover:bg-gray-50"
                      >
                        -
                      </button>
                      <span className="min-w-6 text-center">{i.quantity}</span>
                      <button
                        onClick={() => increase(i.menu_item_id)}
                        className="w-8 h-8 rounded-lg border hover:bg-gray-50"
                      >
                        +
                      </button>

                      <button
                        onClick={() => remove(i.menu_item_id)}
                        className="ml-2 text-sm text-red-600 hover:underline"
                      >
                        Quitar
                      </button>
                    </div>
                  </div>

                  <div className="font-semibold text-gray-900">
                    {formatCOP(i.line_total_cop)}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="p-4 border-t">
          <div className="flex items-center justify-between mb-3">
            <span className="text-gray-700">Subtotal</span>
            <span className="font-semibold">{formatCOP(subtotal)}</span>
          </div>

          <Link
            to="/checkout"
            onClick={onClose}
            className={`w-full inline-flex items-center justify-center rounded-xl px-4 py-3 font-semibold transition ${
              items.length === 0
                ? "pointer-events-none bg-gray-200 text-gray-500"
                : "bg-green-600 text-white hover:bg-green-700"
            }`}
          >
            Continuar al checkout
          </Link>
        </div>
      </div>
    </div>
  );
}
