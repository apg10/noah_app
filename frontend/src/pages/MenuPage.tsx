import React from "react";
import { noahApi } from "../api/noahApi";
import type { MenuItem } from "../types/noah"
import { formatCOP } from "../utils/money";
import { useCartStore } from "../store/cartStore";


export const MenuPage: React.FC = () => {
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  const [categories, setCategories] = React.useState<Category[]>([]);
  const [items, setItems] = React.useState<MenuItem[]>([]);
  const [selectedCategoryId, setSelectedCategoryId] = React.useState<number | "all">("all");

  // Adapter: para no depender 100% de cómo nombraste la función en tu store
  const addItem = useCartStore((s: any) => s.addItem || s.add || s.addToCart);

  React.useEffect(() => {
    const run = async () => {
      try {
        setLoading(true);
        setError(null);

        const [cats, menu] = await Promise.all([
          noahApi.getCategories(),
          noahApi.getMenuItems(),
        ]);

        setCategories(cats);
        setItems(menu);
      } catch (e: any) {
        setError(e?.message || "Error cargando el menú");
      } finally {
        setLoading(false);
      }
    };

    run();
  }, []);

  const filteredItems = React.useMemo(() => {
    if (selectedCategoryId === "all") return items;

    return items.filter((i) => {
      const cat = i.category;
      if (typeof cat === "number") return cat === selectedCategoryId;
      if (typeof cat === "object" && cat?.id) return cat.id === selectedCategoryId;
      return false;
    });
  }, [items, selectedCategoryId]);

  const handleAdd = (item: MenuItem) => {
    if (!addItem) {
      console.warn("No existe addItem/add/addToCart en tu cartStore");
      return;
    }

    addItem({
      menu_item_id: item.id,
      name: item.name,
      unit_price_cop: item.price_cop,
    });
  };

  if (loading) {
    return (
      <div className="py-10">
        <h1 className="text-2xl font-bold text-slate-900 mb-2">Menú</h1>
        <p className="text-slate-600">Cargando productos…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-10">
        <h1 className="text-2xl font-bold text-slate-900 mb-2">Menú</h1>
        <p className="text-red-600 mb-4">Error: {error}</p>
        <p className="text-slate-600">
          Revisa que el backend esté corriendo y que CORS permita localhost:5173.
        </p>
      </div>
    );
  }

  return (
    <div className="py-10">
      <div className="flex items-end justify-between gap-4 flex-wrap mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Menú</h1>
          <p className="text-slate-600">
            Selecciona tus platos y agrégalos al carrito.
          </p>
        </div>

        {/* Filtro por categorías */}
        <div className="flex gap-2 flex-wrap">
          <button
            className={`badge ${selectedCategoryId === "all" ? "badge-pending" : ""}`}
            onClick={() => setSelectedCategoryId("all")}
            type="button"
          >
            Todo
          </button>

          {categories.map((c) => (
            <button
              key={c.id}
              className={`badge ${selectedCategoryId === c.id ? "badge-inprogress" : ""}`}
              onClick={() => setSelectedCategoryId(c.id)}
              type="button"
            >
              {c.name}
            </button>
          ))}
        </div>
      </div>

      {/* Grid */}
      {filteredItems.length === 0 ? (
        <div className="card p-6">
          <p className="text-slate-600">No hay productos en esta categoría.</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filteredItems.map((item) => (
            <div key={item.id} className="card p-5 flex flex-col">
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-slate-900">{item.name}</h3>
                {item.description && (
                  <p className="text-sm text-slate-600 mt-1">{item.description}</p>
                )}

                <div className="mt-3 font-bold text-slate-900">
                  {formatCOP(item.price_cop)}
                </div>
              </div>

              <button
                className="btn-primary mt-4"
                type="button"
                onClick={() => handleAdd(item)}
              >
                Agregar
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
