// Rehan Laptop & Computer - Storefront JavaScript
window.getProductFallbackImage = function(category = "", brand = "REHAN", title = "") {
  const cat = (category || "").toLowerCase();
  const br = (brand || "REHAN").toUpperCase();
  let icon = "💻";
  let bgGradient = "#0f172a, #1e293b";
  if (cat.includes("gaming")) {
    icon = "🎮";
    bgGradient = "#1e1b4b, #312e81";
  } else if (cat.includes("desktop") || cat.includes("cpu")) {
    icon = "🖥️";
    bgGradient = "#042f2e, #134e4a";
  } else if (cat.includes("monitor") || cat.includes("display") || cat.includes("led")) {
    icon = "📺";
    bgGradient = "#172554, #1e40af";
  } else if (cat.includes("repair")) {
    icon = "🔧";
    bgGradient = "#451a03, #78350f";
  } else if (cat.includes("accessory") || cat.includes("mouse") || cat.includes("keyboard") || cat.includes("ssd") || cat.includes("dock") || cat.includes("charger")) {
    icon = "⚡";
    bgGradient = "#3b0764, #581c87";
  }
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="600" height="450" viewBox="0 0 600 450">
    <defs>
      <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="${bgGradient.split(',')[0].trim()}"/>
        <stop offset="100%" stop-color="${bgGradient.split(',')[1].trim()}"/>
      </linearGradient>
    </defs>
    <rect width="600" height="450" fill="url(#g)"/>
    <circle cx="300" cy="180" r="80" fill="#ffffff" fill-opacity="0.08"/>
    <text x="300" y="205" font-size="75" text-anchor="middle" dominant-baseline="middle">${icon}</text>
    <rect x="170" y="295" width="260" height="38" rx="19" fill="#f59e0b" fill-opacity="0.95"/>
    <text x="300" y="320" font-size="16" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif" font-weight="900" fill="#0f172a" text-anchor="middle" letter-spacing="2">${br}</text>
    <text x="300" y="370" font-size="14" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif" font-weight="600" fill="#94a3b8" text-anchor="middle">REHAN LAPTOP &amp; COMPUTER</text>
    <text x="300" y="400" font-size="12" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif" font-weight="500" fill="#64748b" text-anchor="middle">Shop #96 Trust Plaza Sargodha</text>
  </svg>`;
  return "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
};

document.addEventListener("DOMContentLoaded", () => {
  // State
  let storeInfo = {};
  let categories = [];
  let brands = [];
  let allProducts = [];
  let cart = JSON.parse(localStorage.getItem("rehan_cart") || "[]");

  // DOM Elements
  const productsGrid = document.getElementById("productsGrid");
  const productTotalCount = document.getElementById("productTotalCount");
  const noProductsFound = document.getElementById("noProductsFound");
  const globalSearchInput = document.getElementById("globalSearchInput");
  const mobileSearchInput = document.getElementById("mobileSearchInput");
  const clearSearchBtn = document.getElementById("clearSearchBtn");
  const filterCategory = document.getElementById("filterCategory");
  const filterBrand = document.getElementById("filterBrand");
  const filterCondition = document.getElementById("filterCondition");
  const filterPurpose = document.getElementById("filterPurpose");
  const sortProducts = document.getElementById("sortProducts");
  const resetFiltersBtn = document.getElementById("resetFiltersBtn");
  const brandsStrip = document.getElementById("brandsStrip");

  // Cart Elements
  const cartToggleBtn = document.getElementById("cartToggleBtn");
  const closeCartBtn = document.getElementById("closeCartBtn");
  const cartDrawer = document.getElementById("cartDrawer");
  const cartDrawerBackdrop = document.getElementById("cartDrawerBackdrop");
  const cartCountBadge = document.getElementById("cartCountBadge");
  const drawerCount = document.getElementById("drawerCount");
  const cartItemsContainer = document.getElementById("cartItemsContainer");
  const cartSubtotal = document.getElementById("cartSubtotal");
  const cartShippingFee = document.getElementById("cartShippingFee");
  const cartTotalPayable = document.getElementById("cartTotalPayable");
  const proceedToCheckoutBtn = document.getElementById("proceedToCheckoutBtn");

  // Checkout Elements
  const checkoutModal = document.getElementById("checkoutModal");
  const closeCheckoutBtn = document.getElementById("closeCheckoutBtn");
  const checkoutForm = document.getElementById("checkoutForm");
  const chkBtnTotal = document.getElementById("chkBtnTotal");
  const orderSuccessView = document.getElementById("orderSuccessView");
  const successOrderNum = document.getElementById("successOrderNum");
  const dismissOrderSuccessBtn = document.getElementById("dismissOrderSuccessBtn");

  // Product Detail Modal
  const productDetailModal = document.getElementById("productDetailModal");
  const closeDetailModalBtn = document.getElementById("closeDetailModalBtn");
  const productDetailContent = document.getElementById("productDetailContent");

  // Forms & Portals
  const repairBookingForm = document.getElementById("repairBookingForm");
  const repairSuccessMsg = document.getElementById("repairSuccessMsg");
  const tradeInForm = document.getElementById("tradeInForm");
  const tradeInSuccessMsg = document.getElementById("tradeInSuccessMsg");
  const trackerInput = document.getElementById("trackerInput");
  const trackSearchBtn = document.getElementById("trackSearchBtn");
  const trackerResults = document.getElementById("trackerResults");
  const mobileMenuBtn = document.getElementById("mobileMenuBtn");
  const mobileMenuDropdown = document.getElementById("mobileMenuDropdown");

  // Staff Gateway Modal Elements
  const staffGatewayModal = document.getElementById("staffGatewayModal");
  const adminGatewayBtn = document.getElementById("adminGatewayBtn");
  const closeStaffModalBtn = document.getElementById("closeStaffModalBtn");
  const staffLoginForm = document.getElementById("staffLoginForm");
  const staffUser = document.getElementById("staffUser");
  const staffPass = document.getElementById("staffPass");
  const staffErrorMsg = document.getElementById("staffErrorMsg");
  const brandLogoTrigger = document.getElementById("brandLogoTrigger");

  // 1. Initial Load
  init();

  async function init() {
    setupMobileMenu();
    setupCartEvents();
    setupFilterEvents();
    setupForms();
    setupStaffGateway();
    sendVisitorPing();

    await loadStoreInfo();
    await loadCategories();
    await loadBrands();
    await loadProducts();
    updateCartUI();
  }

  // Visitor Tracking & Access Enforcement Beacon
  async function sendVisitorPing() {
    try {
      let sessionId = sessionStorage.getItem("rc_visitor_sess");
      if (!sessionId) {
        sessionId = "v_" + Math.random().toString(36).substring(2, 12);
        sessionStorage.setItem("rc_visitor_sess", sessionId);
      }

      const res = await fetch("/api/public/visitor/ping", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          page_url: window.location.pathname + window.location.hash,
          page_title: document.title,
          referrer: document.referrer || "Direct",
          session_id: sessionId,
          device_type: window.innerWidth < 768 ? "Mobile" : (window.innerWidth < 1024 ? "Tablet" : "Desktop")
        })
      });
      const data = await res.json();

      // If IP has been restricted by Admin
      if (data.blocked) {
        document.body.innerHTML = `
          <div style="min-height: 100vh; display: flex; align-items: center; justify-content: center; background: #090d16; color: #fff; text-align: center; font-family: sans-serif; padding: 24px;">
            <div style="max-width: 480px; background: #131b2e; border: 1px solid #334155; padding: 36px; rounded: 24px; border-radius: 20px; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);">
              <div style="font-size: 52px; margin-bottom: 16px;">🛡️</div>
              <h1 style="font-size: 22px; font-weight: 800; margin-bottom: 8px; color: #f87171;">Access Restricted</h1>
              <p style="color: #94a3b8; font-size: 13px; line-height: 1.6; margin-bottom: 20px;">${data.reason || 'This network IP address has been restricted by store administration.'}</p>
              <div style="padding: 12px; background: #1e293b; border-radius: 12px; font-size: 11px; color: #cbd5e1;">
                For assistance, contact Rehan Computers helpdesk: <br>
                <strong style="color: #fbbf24;">0300-9607829</strong> | Shop #96, 1st Floor, Trust Plaza, Sargodha
              </div>
            </div>
          </div>
        `;
      }
    } catch (err) {
      // Non-blocking background analytics
    }
  }

  function setupMobileMenu() {
    if (mobileMenuBtn && mobileMenuDropdown) {
      mobileMenuBtn.addEventListener("click", () => {
        mobileMenuDropdown.classList.toggle("hidden");
      });
    }
  }

  // 2. Staff Gateway Handling (Hidden from regular shoppers)
  function setupStaffGateway() {
    const openStaffModal = () => {
      staffErrorMsg.classList.add("hidden");
      staffGatewayModal.classList.remove("hidden");
      staffPass.focus();
    };

    const closeStaffModal = () => {
      staffGatewayModal.classList.add("hidden");
    };

    if (adminGatewayBtn) adminGatewayBtn.addEventListener("click", openStaffModal);
    if (closeStaffModalBtn) closeStaffModalBtn.addEventListener("click", closeStaffModal);

    // Double-click logo triggers staff login
    if (brandLogoTrigger) {
      brandLogoTrigger.addEventListener("dblclick", (e) => {
        e.preventDefault();
        openStaffModal();
      });
    }

    // Secret Hotkey Shortcut: Ctrl + Shift + A
    window.addEventListener("keydown", (e) => {
      if (e.ctrlKey && e.shiftKey && (e.key === "A" || e.key === "a")) {
        e.preventDefault();
        openStaffModal();
      }
    });

    if (staffLoginForm) {
      staffLoginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        staffErrorMsg.classList.add("hidden");

        const username = staffUser.value.trim();
        const password = staffPass.value.trim();

        const submitBtn = document.getElementById("staffSubmitBtn");
        submitBtn.disabled = true;
        submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin mr-2"></i> Verifying Credentials...`;

        try {
          const res = await fetch("/api/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username_or_email: username, password: password })
          });
          const data = await res.json();

          if (!res.ok) {
            throw new Error(data.detail || "Invalid authorization credentials");
          }

          // Save credentials in localStorage
          localStorage.setItem("rehan_token", data.access_token);
          localStorage.setItem("rehan_user", JSON.stringify(data.user));

          // Redirect securely to ERP portal
          window.location.href = "/admin";
        } catch (err) {
          staffErrorMsg.textContent = err.message;
          staffErrorMsg.classList.remove("hidden");
        } finally {
          submitBtn.disabled = false;
          submitBtn.innerHTML = `<span>Authorize & Enter ERP</span><i class="fa-solid fa-arrow-right text-amber-400"></i>`;
        }
      });
    }
  }

  // 3. Load Store Information
  async function loadStoreInfo() {
    try {
      const res = await fetch("/api/public/store-info");
      storeInfo = await res.json();
    } catch (err) {
      console.error("Failed to load store info", err);
    }
  }

  async function loadCategories() {
    try {
      const res = await fetch("/api/public/categories");
      categories = await res.json();
      filterCategory.innerHTML = '<option value="">All Categories</option>';
      categories.forEach(c => {
        const opt = document.createElement("option");
        opt.value = c.slug;
        opt.textContent = c.name;
        filterCategory.appendChild(opt);
      });
    } catch (err) {
      console.error("Failed to load categories", err);
    }
  }

  async function loadBrands() {
    try {
      const res = await fetch("/api/public/brands");
      brands = await res.json();
      filterBrand.innerHTML = '<option value="">All Manufacturers</option>';
      brandsStrip.innerHTML = "";

      brands.forEach(b => {
        const opt = document.createElement("option");
        opt.value = b.slug;
        opt.textContent = b.name;
        filterBrand.appendChild(opt);

        // Strip pill
        const pill = document.createElement("button");
        pill.className = "text-xs font-black px-3.5 py-1.5 rounded-full border border-slate-200 text-slate-700 hover:border-brand-700 hover:text-brand-900 hover:bg-brand-50 transition";
        pill.textContent = b.name.toUpperCase();
        pill.onclick = () => {
          filterBrand.value = b.slug;
          loadProducts();
          document.getElementById("catalogSection").scrollIntoView({ behavior: "smooth" });
        };
        brandsStrip.appendChild(pill);
      });
    } catch (err) {
      console.error("Failed to load brands", err);
    }
  }

  async function loadProducts() {
    productsGrid.innerHTML = `
      <div class="col-span-full py-12 text-center text-slate-400">
        <i class="fa-solid fa-spinner fa-spin text-2xl text-brand-900 mb-2"></i>
        <p class="text-xs">Querying live inventory from Shop #96 Trust Plaza...</p>
      </div>
    `;

    const searchVal = globalSearchInput.value.trim() || mobileSearchInput.value.trim();
    const catVal = filterCategory.value;
    const brandVal = filterBrand.value;
    const condVal = filterCondition.value;
    const sortVal = sortProducts.value;

    const params = new URLSearchParams();
    if (searchVal) params.append("search", searchVal);
    if (catVal) params.append("category", catVal);
    if (brandVal) params.append("brand", brandVal);
    if (condVal) params.append("condition", condVal);
    if (sortVal) params.append("sort", sortVal);

    try {
      const res = await fetch(`/api/public/products?${params.toString()}`);
      allProducts = await res.json();
      
      // Ensure Laptops are at the top and accessories are at the last
      if (!sortVal || sortVal === "newest") {
        const getCatPriority = (p) => {
          const c = (p.category_slug || p.category_name || "").toLowerCase();
          if (c.includes("laptop")) return 1;
          if (c.includes("desktop") || c.includes("cpu")) return 2;
          if (c.includes("monitor") || c.includes("display") || c.includes("led")) return 3;
          if (c.includes("repair")) return 4;
          return 5; // accessories & parts at the last
        };
        allProducts.sort((a, b) => {
          const pa = getCatPriority(a);
          const pb = getCatPriority(b);
          if (pa !== pb) return pa - pb;
          if ((b.is_featured || 0) !== (a.is_featured || 0)) return (b.is_featured || 0) - (a.is_featured || 0);
          return a.id - b.id;
        });
      }

      applyPurposeFilter();
      renderProducts();
    } catch (err) {
      console.error("Failed to load products", err);
      productsGrid.innerHTML = `<p class="col-span-full text-center text-red-500 text-xs">Error loading hardware products.</p>`;
    }
  }

  function applyPurposeFilter() {
    const purpose = filterPurpose.value;
    if (!purpose) return;

    allProducts = allProducts.filter(p => {
      const title = (p.title || "").toLowerCase();
      const specsStr = JSON.stringify(p.specs || {}).toLowerCase();
      const combined = `${title} ${specsStr}`;

      if (purpose === "student") {
        return p.selling_price <= 65000 || combined.includes("i5") || combined.includes("i3") || combined.includes("t480");
      } else if (purpose === "freelance") {
        return combined.includes("16gb") || combined.includes("i7") || combined.includes("thinkpad") || combined.includes("elitebook") || combined.includes("macbook");
      } else if (purpose === "gaming") {
        return combined.includes("gaming") || combined.includes("rtx") || combined.includes("gtx") || combined.includes("144hz") || combined.includes("mechanical") || combined.includes("headset");
      } else if (purpose === "workstation") {
        return combined.includes("precision") || combined.includes("quadro") || combined.includes("workstation") || combined.includes("32gb") || combined.includes("nvme");
      }
      return true;
    });
  }

  // 4. Render Products Grid
  function renderProducts() {
    productTotalCount.textContent = `${allProducts.length} Items Available`;

    if (allProducts.length === 0) {
      productsGrid.innerHTML = "";
      noProductsFound.classList.remove("hidden");
      return;
    }

    noProductsFound.classList.add("hidden");
    productsGrid.innerHTML = "";

    allProducts.forEach(prod => {
      const card = createProductCard(prod);
      productsGrid.appendChild(card);
    });
  }

  function createProductCard(prod) {
    const card = document.createElement("div");
    card.className = "bg-white rounded-2xl border border-slate-200/90 overflow-hidden product-card flex flex-col justify-between group";

    const currentPrice = prod.discount_price && prod.discount_price > 0 ? prod.discount_price : prod.selling_price;
    const hasDiscount = prod.discount_price && prod.discount_price > 0 && prod.discount_price < prod.selling_price;

    let specsHtml = "";
    if (prod.specs && typeof prod.specs === "object") {
      const s = prod.specs;
      const pills = [];
      if (s.processor) pills.push(s.processor.split("(")[0].replace("Intel ", "").trim());
      if (s.ram) pills.push(s.ram.split("(")[0].trim());
      if (s.storage) pills.push(s.storage.split("+")[0].trim());
      if (s.display) pills.push(s.display.split("(")[0].trim());
      if (s.speed) pills.push(s.speed.split("(")[0].trim());
      if (s.sensor) pills.push(s.sensor.split("(")[0].trim());
      if (s.switches) pills.push(s.switches.split("(")[0].trim());
      if (s.drivers) pills.push(s.drivers.split("(")[0].trim());

      specsHtml = pills.slice(0, 3).map(pill => 
        `<span class="inline-block bg-slate-100 text-slate-700 text-[10px] font-semibold px-2 py-0.5 rounded-md truncate max-w-[130px]">${pill}</span>`
      ).join(" ");
    }

    const conditionBadgeClass = prod.condition === "Brand New" ? "badge-brand-new" : "badge-grade";

    card.innerHTML = `
      <div>
        <!-- Image & Badges -->
        <div class="relative aspect-[4/3] bg-slate-100 overflow-hidden cursor-pointer product-img-trigger">
          <img 
            src="${prod.image_url || window.getProductFallbackImage(prod.category_name, prod.brand_name, prod.title)}" 
            alt="${prod.title}" 
            class="w-full h-full object-cover group-hover:scale-105 transition duration-300"
            loading="lazy"
            onerror="this.onerror=null; this.src=window.getProductFallbackImage('${(prod.category_name || '').replace(/['\"]/g, '')}', '${(prod.brand_name || '').replace(/['\"]/g, '')}', '${(prod.title || '').replace(/['\"]/g, '')}');"
          >
          <div class="absolute top-2.5 left-2.5 flex flex-col gap-1 items-start">
            <span class="text-[10px] font-extrabold px-2.5 py-0.5 rounded-full ${conditionBadgeClass} shadow-sm">
              ${prod.condition}
            </span>
            ${hasDiscount ? `<span class="text-[10px] font-black px-2 py-0.5 rounded-full bg-red-600 text-white shadow-sm">SALE</span>` : ''}
          </div>
          <div class="absolute top-2.5 right-2.5">
            <span class="text-[9px] font-bold px-2 py-0.5 rounded-full bg-slate-900/80 text-white backdrop-blur-sm">
              ${prod.brand_name || 'Verified'}
            </span>
          </div>
        </div>

        <!-- Content -->
        <div class="p-4 space-y-2.5">
          <div class="text-[10px] font-mono text-slate-400 uppercase tracking-wider">${prod.sku}</div>
          <h3 class="text-sm font-bold text-slate-900 group-hover:text-brand-900 transition line-clamp-2 cursor-pointer product-title-trigger">
            ${prod.title}
          </h3>

          <div class="flex flex-wrap gap-1 pt-0.5">
            ${specsHtml}
          </div>

          <div class="text-[11px] text-amber-800 font-semibold flex items-center gap-1.5 pt-1">
            <i class="fa-solid fa-shield-halved text-amber-600"></i>
            <span>${prod.warranty_period || 'Checking Guarantee'}</span>
          </div>
        </div>
      </div>

      <!-- Pricing & Actions Footer -->
      <div class="p-4 pt-0 border-t border-slate-100 mt-2 space-y-3">
        <div class="flex items-baseline justify-between pt-2">
          <div>
            <span class="text-xs text-slate-400 font-bold">PKR</span>
            <span class="text-lg font-black text-brand-950">${currentPrice.toLocaleString()}</span>
            ${hasDiscount ? `<span class="text-xs text-slate-400 line-through ml-1">${prod.selling_price.toLocaleString()}</span>` : ''}
          </div>
          <span class="text-[10px] font-bold ${prod.stock_quantity > 0 ? 'text-emerald-700 bg-emerald-50' : 'text-red-700 bg-red-50'} px-2 py-0.5 rounded">
            ${prod.stock_quantity > 0 ? `${prod.stock_quantity} Ready` : 'Backordered'}
          </span>
        </div>

        <div class="grid grid-cols-2 gap-2">
          <button class="add-to-cart-btn w-full bg-slate-100 hover:bg-brand-900 hover:text-white text-slate-800 font-bold py-2 rounded-xl text-xs transition flex items-center justify-center gap-1.5">
            <i class="fa-solid fa-cart-plus"></i> Add Cart
          </button>
          <a 
            href="https://wa.me/923009607829?text=${encodeURIComponent('Assalam-o-Alaikum Rehan Computers Sargodha! I want to inquire about: ' + prod.title + ' (SKU: ' + prod.sku + ') priced at PKR ' + currentPrice.toLocaleString())}" 
            target="_blank" 
            class="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-2 rounded-xl text-xs transition flex items-center justify-center gap-1 shadow-sm"
          >
            <i class="fa-brands fa-whatsapp text-sm"></i> WhatsApp
          </a>
        </div>
      </div>
    `;

    const triggerDetail = () => showProductDetail(prod.id);
    card.querySelector(".product-img-trigger").addEventListener("click", triggerDetail);
    card.querySelector(".product-title-trigger").addEventListener("click", triggerDetail);

    card.querySelector(".add-to-cart-btn").addEventListener("click", (e) => {
      e.stopPropagation();
      addToCart(prod);
    });

    return card;
  }

  // 5. Product Details Modal
  async function showProductDetail(productId) {
    try {
      const res = await fetch(`/api/public/products/${productId}`);
      const prod = await res.json();

      const currentPrice = prod.discount_price && prod.discount_price > 0 ? prod.discount_price : prod.selling_price;
      const hasDiscount = prod.discount_price && prod.discount_price > 0 && prod.discount_price < prod.selling_price;

      let specsRows = "";
      if (prod.specs && typeof prod.specs === "object") {
        for (const [key, val] of Object.entries(prod.specs)) {
          specsRows += `
            <tr class="border-b border-slate-100">
              <td class="py-2 pr-3 font-bold text-slate-500 capitalize w-1/3 text-xs">${key.replace("_", " ")}</td>
              <td class="py-2 text-slate-800 font-medium text-xs">${val}</td>
            </tr>
          `;
        }
      }

      productDetailContent.innerHTML = `
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
          <div class="space-y-3">
            <div class="aspect-[4/3] rounded-xl overflow-hidden bg-slate-100 border border-slate-200">
              <img 
                src="${prod.image_url || window.getProductFallbackImage(prod.category_name, prod.brand_name, prod.title)}" 
                alt="${prod.title}" 
                class="w-full h-full object-cover"
                onerror="this.onerror=null; this.src=window.getProductFallbackImage('${(prod.category_name || '').replace(/['\"]/g, '')}', '${(prod.brand_name || '').replace(/['\"]/g, '')}', '${(prod.title || '').replace(/['\"]/g, '')}');"
              >
            </div>
            <div class="p-3 bg-amber-50 rounded-xl border border-amber-200 text-amber-900 text-xs flex items-center gap-2">
              <i class="fa-solid fa-location-dot text-amber-600 text-sm"></i>
              <span>Available for physical bench inspection at <strong>Shop #96 Trust Plaza Sargodha</strong></span>
            </div>
          </div>

          <div class="space-y-4">
            <div>
              <div class="flex items-center gap-2 mb-1">
                <span class="text-[10px] font-black uppercase tracking-wider px-2.5 py-0.5 rounded-full badge-grade">${prod.condition}</span>
                <span class="text-[10px] font-mono text-slate-400">${prod.sku}</span>
              </div>
              <h2 class="text-lg font-black text-slate-900">${prod.title}</h2>
            </div>

            <div class="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-baseline justify-between">
              <div>
                <span class="text-xs text-slate-400 font-bold">Price:</span>
                <span class="text-2xl font-black text-brand-950 ml-1">PKR ${currentPrice.toLocaleString()}</span>
                ${hasDiscount ? `<span class="text-xs text-slate-400 line-through ml-2">${prod.selling_price.toLocaleString()}</span>` : ''}
              </div>
              <span class="text-xs font-bold text-emerald-700 bg-emerald-100 px-2.5 py-1 rounded-full">
                ${prod.warranty_period}
              </span>
            </div>

            <div class="max-h-52 overflow-y-auto pr-1">
              <table class="w-full text-left">
                <tbody>
                  ${specsRows}
                </tbody>
              </table>
            </div>

            <div class="grid grid-cols-2 gap-3 pt-2">
              <button id="modalAddToCartBtn" class="w-full bg-brand-900 hover:bg-brand-800 text-white font-bold py-3 rounded-xl text-xs transition flex items-center justify-center gap-2 shadow-md">
                <i class="fa-solid fa-cart-plus"></i> Add to Cart
              </button>
              <a 
                href="https://wa.me/923009607829?text=${encodeURIComponent('Assalam-o-Alaikum Rehan Computers Sargodha! I want to buy: ' + prod.title + ' (SKU: ' + prod.sku + ') at Trust Plaza')}" 
                target="_blank" 
                class="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3 rounded-xl text-xs transition flex items-center justify-center gap-2 shadow-md"
              >
                <i class="fa-brands fa-whatsapp text-base"></i> WhatsApp Order
              </a>
            </div>
          </div>
        </div>
      `;

      document.getElementById("modalAddToCartBtn").onclick = () => {
        addToCart(prod);
        closeProductModal();
      };

      productDetailModal.classList.remove("hidden");
    } catch (err) {
      console.error("Failed to load product detail", err);
    }
  }

  function closeProductModal() {
    productDetailModal.classList.add("hidden");
  }

  if (closeDetailModalBtn) closeDetailModalBtn.onclick = closeProductModal;
  productDetailModal.onclick = (e) => {
    if (e.target === productDetailModal) closeProductModal();
  };

  // 6. Cart Logic
  function addToCart(product) {
    const existing = cart.find(item => item.id === product.id);
    if (existing) {
      existing.quantity += 1;
    } else {
      const price = product.discount_price && product.discount_price > 0 ? product.discount_price : product.selling_price;
      cart.push({
        id: product.id,
        title: product.title,
        sku: product.sku,
        unit_price: price,
        image_url: product.image_url,
        quantity: 1
      });
    }
    saveCart();
    updateCartUI();
    openCartDrawer();
  }

  function updateCartUI() {
    const totalCount = cart.reduce((acc, it) => acc + it.quantity, 0);
    cartCountBadge.textContent = totalCount;
    drawerCount.textContent = totalCount;

    if (cart.length === 0) {
      cartItemsContainer.innerHTML = `
        <div class="text-center py-12 text-slate-400">
          <i class="fa-solid fa-cart-shopping text-3xl mb-2 text-slate-300"></i>
          <p class="text-xs font-bold">Your cart is empty</p>
          <p class="text-[11px] text-slate-400 mt-1">Browse laptops & gear to add items</p>
        </div>
      `;
      cartSubtotal.textContent = "PKR 0";
      cartShippingFee.textContent = "Free in Sargodha";
      cartTotalPayable.textContent = "PKR 0";
      proceedToCheckoutBtn.disabled = true;
      proceedToCheckoutBtn.classList.add("opacity-50", "cursor-not-allowed");
      return;
    }

    proceedToCheckoutBtn.disabled = false;
    proceedToCheckoutBtn.classList.remove("opacity-50", "cursor-not-allowed");

    let subtotal = 0;
    cartItemsContainer.innerHTML = "";

    cart.forEach(item => {
      const itemTotal = item.unit_price * item.quantity;
      subtotal += itemTotal;

      const itemEl = document.createElement("div");
      itemEl.className = "flex items-center gap-3 bg-slate-50 p-3 rounded-xl border border-slate-200";
      itemEl.innerHTML = `
        <img 
          src="${item.image_url || window.getProductFallbackImage(item.category_name, item.brand_name, item.title)}" 
          alt="${item.title}" 
          class="w-14 h-14 rounded-lg object-cover bg-white border border-slate-200"
          onerror="this.onerror=null; this.src=window.getProductFallbackImage('${(item.category_name || '').replace(/['\"]/g, '')}', '${(item.brand_name || '').replace(/['\"]/g, '')}', '${(item.title || '').replace(/['\"]/g, '')}');"
        >
        <div class="flex-1 min-w-0">
          <h4 class="text-xs font-bold text-slate-900 truncate">${item.title}</h4>
          <div class="text-[11px] text-brand-900 font-black">PKR ${item.unit_price.toLocaleString()}</div>
          <div class="flex items-center gap-2 mt-1">
            <button class="cart-minus w-5 h-5 rounded bg-white border border-slate-300 flex items-center justify-center text-xs font-bold text-slate-600 hover:bg-slate-100">-</button>
            <span class="text-xs font-bold text-slate-800">${item.quantity}</span>
            <button class="cart-plus w-5 h-5 rounded bg-white border border-slate-300 flex items-center justify-center text-xs font-bold text-slate-600 hover:bg-slate-100">+</button>
          </div>
        </div>
        <button class="cart-remove text-slate-400 hover:text-red-600 p-1">
          <i class="fa-regular fa-trash-can text-sm"></i>
        </button>
      `;

      itemEl.querySelector(".cart-minus").onclick = () => {
        if (item.quantity > 1) {
          item.quantity -= 1;
        } else {
          cart = cart.filter(x => x.id !== item.id);
        }
        saveCart();
        updateCartUI();
      };

      itemEl.querySelector(".cart-plus").onclick = () => {
        item.quantity += 1;
        saveCart();
        updateCartUI();
      };

      itemEl.querySelector(".cart-remove").onclick = () => {
        cart = cart.filter(x => x.id !== item.id);
        saveCart();
        updateCartUI();
      };

      cartItemsContainer.appendChild(itemEl);
    });

    const shipping = subtotal >= 25000 ? 0 : 300;
    const totalPayable = subtotal + shipping;

    cartSubtotal.textContent = `PKR ${subtotal.toLocaleString()}`;
    cartShippingFee.textContent = shipping === 0 ? "FREE (Promotional)" : `PKR ${shipping}`;
    cartTotalPayable.textContent = `PKR ${totalPayable.toLocaleString()}`;
    chkBtnTotal.textContent = `PKR ${totalPayable.toLocaleString()}`;
  }

  function saveCart() {
    localStorage.setItem("rehan_cart", JSON.stringify(cart));
  }

  function openCartDrawer() {
    cartDrawerBackdrop.classList.remove("hidden");
    cartDrawer.classList.remove("translate-x-full");
  }

  function closeCartDrawer() {
    cartDrawer.classList.add("translate-x-full");
    cartDrawerBackdrop.classList.add("hidden");
  }

  function setupCartEvents() {
    if (cartToggleBtn) cartToggleBtn.onclick = openCartDrawer;
    if (closeCartBtn) closeCartBtn.onclick = closeCartDrawer;
    if (cartDrawerBackdrop) cartDrawerBackdrop.onclick = closeCartDrawer;

    if (proceedToCheckoutBtn) {
      proceedToCheckoutBtn.onclick = () => {
        closeCartDrawer();
        checkoutModal.classList.remove("hidden");
      };
    }

    if (closeCheckoutBtn) {
      closeCheckoutBtn.onclick = () => checkoutModal.classList.add("hidden");
    }

    if (dismissOrderSuccessBtn) {
      dismissOrderSuccessBtn.onclick = () => {
        checkoutModal.classList.add("hidden");
        orderSuccessView.classList.add("hidden");
        checkoutForm.classList.remove("hidden");
      };
    }
  }

  // 7. Checkout Order Submission
  checkoutForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    if (cart.length === 0) {
      alert("Your cart is empty!");
      return;
    }

    const payload = {
      customer_name: document.getElementById("chkName").value.trim(),
      customer_phone: document.getElementById("chkPhone").value.trim(),
      city: document.getElementById("chkCity").value.trim() || "Sargodha",
      shipping_address: document.getElementById("chkAddress").value.trim(),
      payment_method: document.querySelector('input[name="paymentMethod"]:checked')?.value || "cash_on_delivery",
      items: cart.map(it => ({ product_id: it.id, quantity: it.quantity }))
    };

    const submitBtn = checkoutForm.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin mr-2"></i> Registering Order...`;

    try {
      const res = await fetch("/api/public/orders", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Failed to place order");
      }

      // Success
      cart = [];
      saveCart();
      updateCartUI();

      successOrderNum.textContent = data.order_number;
      checkoutForm.classList.add("hidden");
      orderSuccessView.classList.remove("hidden");
    } catch (err) {
      alert("Error: " + err.message);
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = `Confirm Order (<span id="chkBtnTotal">PKR ${cartTotalPayable.textContent}</span>)`;
    }
  });

  // 8. Filter Events
  function setupFilterEvents() {
    let debounceTimer;
    const handleSearch = () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        loadProducts();
      }, 350);
    };

    globalSearchInput.addEventListener("input", handleSearch);
    mobileSearchInput.addEventListener("input", handleSearch);

    filterCategory.addEventListener("change", loadProducts);
    filterBrand.addEventListener("change", loadProducts);
    filterCondition.addEventListener("change", loadProducts);
    filterPurpose.addEventListener("change", () => {
      applyPurposeFilter();
      renderProducts();
    });
    sortProducts.addEventListener("change", loadProducts);

    resetFiltersBtn.addEventListener("click", () => {
      globalSearchInput.value = "";
      mobileSearchInput.value = "";
      filterCategory.value = "";
      filterBrand.value = "";
      filterCondition.value = "";
      filterPurpose.value = "";
      sortProducts.value = "newest";
      loadProducts();
    });
  }

  // 9. Forms (Repair & Trade-In & Tracking)
  function setupForms() {
    repairBookingForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const payload = {
        customer_name: document.getElementById("repName").value.trim(),
        customer_phone: document.getElementById("repPhone").value.trim(),
        device_brand: document.getElementById("repBrand").value,
        device_model: document.getElementById("repModel").value.trim(),
        problem_description: document.getElementById("repIssue").value.trim(),
        accessories_received: document.getElementById("repAccessories").value.trim() || "None"
      };

      const btn = repairBookingForm.querySelector('button[type="submit"]');
      btn.disabled = true;
      btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin mr-2"></i> Registering Lab Ticket...`;

      try {
        const res = await fetch("/api/public/repairs", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Failed to register repair ticket");

        repairBookingForm.reset();
        repairSuccessMsg.classList.remove("hidden");
        repairSuccessMsg.innerHTML = `
          <div class="flex items-center gap-2 font-bold mb-1">
            <i class="fa-solid fa-circle-check text-emerald-600 text-base"></i>
            <span>Repair Job Ticket Created!</span>
          </div>
          <p>Your tracking reference code: <strong class="font-mono text-brand-900 text-sm">${data.ticket_number}</strong></p>
          <p class="mt-1">Please bring your machine to <strong>Shop #96, 1st Floor, Trust Plaza, Sargodha</strong>, or contact <strong>0300-9607829</strong> for diagnostic confirmation.</p>
        `;
      } catch (err) {
        alert("Error: " + err.message);
      } finally {
        btn.disabled = false;
        btn.innerHTML = `<i class="fa-solid fa-ticket mr-2 text-amber-400"></i> Register Job Ticket & Reserve Bench Slot`;
      }
    });

    // Trade-In Form
    tradeInForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const payload = {
        customer_name: document.getElementById("trdName").value.trim(),
        customer_phone: document.getElementById("trdPhone").value.trim(),
        device_brand: document.getElementById("trdBrand").value.trim(),
        device_model: document.getElementById("trdModel").value.trim(),
        specs_details: document.getElementById("trdModel").value.trim(),
        condition_grade: document.getElementById("trdCondition").value,
        customer_expected_price: parseFloat(document.getElementById("trdExpected").value) || null
      };

      const btn = tradeInForm.querySelector('button[type="submit"]');
      btn.disabled = true;
      btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin mr-2"></i> Submitting Appraisal...`;

      try {
        const res = await fetch("/api/public/trade-in", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Failed to submit request");

        tradeInForm.reset();
        tradeInSuccessMsg.classList.remove("hidden");
        tradeInSuccessMsg.innerHTML = `
          <div class="flex items-center gap-2 font-bold mb-1">
            <i class="fa-solid fa-circle-check text-emerald-600 text-base"></i>
            <span>Appraisal Submitted! Reference: ${data.request_code}</span>
          </div>
          <p>Our valuation engineer at Shop #96 Trust Plaza will review your hardware specifications and call you at your WhatsApp number shortly.</p>
        `;
      } catch (err) {
        alert("Error: " + err.message);
      } finally {
        btn.disabled = false;
        btn.innerHTML = `<i class="fa-solid fa-calculator mr-2"></i> Request Appraisal Quote`;
      }
    });

    // Tracking Lookup
    trackSearchBtn.addEventListener("click", performTracking);
    trackerInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") performTracking();
    });
  }

  async function performTracking() {
    const key = trackerInput.value.trim();
    if (!key) {
      alert("Please enter an Order Reference, Repair Ticket, or Phone Number");
      return;
    }

    trackSearchBtn.disabled = true;
    trackSearchBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin mr-2"></i> Querying...`;
    trackerResults.classList.remove("hidden");
    trackerResults.innerHTML = `<p class="text-xs text-slate-400 text-center py-4">Checking database...</p>`;

    let foundAny = false;
    let htmlOutput = "";

    // 1. Orders
    try {
      const orderRes = await fetch(`/api/public/orders/track/${encodeURIComponent(key)}`);
      if (orderRes.ok) {
        const orders = await orderRes.json();
        if (orders && orders.length > 0) {
          foundAny = true;
          orders.forEach(ord => {
            const statusStep = getOrderStatusStep(ord.order_status);
            htmlOutput += `
              <div class="p-4 bg-slate-50 rounded-xl border border-slate-200 mb-3 space-y-3">
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-1 pb-2 border-b border-slate-200">
                  <div>
                    <span class="text-xs font-black uppercase text-brand-900">${ord.order_number}</span>
                    <span class="text-[10px] text-slate-500 ml-2">Ordered: ${new Date(ord.created_at).toLocaleDateString()}</span>
                  </div>
                  <span class="text-xs font-bold px-2.5 py-0.5 rounded-full ${getStatusBadgeClass(ord.order_status)} self-start sm:self-auto">
                    ${ord.order_status.toUpperCase()}
                  </span>
                </div>

                <div class="grid grid-cols-4 text-center text-[10px] font-bold text-slate-600 gap-1 pt-1">
                  <div class="${statusStep >= 1 ? 'text-brand-900 font-black' : 'text-slate-400'}">1. Verified</div>
                  <div class="${statusStep >= 2 ? 'text-brand-900 font-black' : 'text-slate-400'}">2. Processing</div>
                  <div class="${statusStep >= 3 ? 'text-brand-900 font-black' : 'text-slate-400'}">3. Dispatched</div>
                  <div class="${statusStep >= 4 ? 'text-emerald-700 font-black' : 'text-slate-400'}">4. Delivered</div>
                </div>

                <div class="text-xs text-slate-700 space-y-1 pt-1">
                  <div><strong>Customer:</strong> ${ord.customer_name} (${ord.customer_phone})</div>
                  <div><strong>Destination:</strong> ${ord.shipping_address}, ${ord.city}</div>
                  ${ord.courier_name ? `<div><strong>Courier:</strong> ${ord.courier_name} (Tracking: <code>${ord.courier_tracking_no || 'Assigned'}</code>)</div>` : ''}
                  <div><strong>Total Value:</strong> PKR ${ord.total_amount.toLocaleString()} (${ord.payment_method})</div>
                </div>
              </div>
            `;
          });
        }
      }
    } catch (e) {
      // Continue
    }

    // 2. Repairs
    try {
      const repRes = await fetch(`/api/public/repairs/track/${encodeURIComponent(key)}`);
      if (repRes.ok) {
        const repairs = await repRes.json();
        if (repairs && repairs.length > 0) {
          foundAny = true;
          repairs.forEach(rep => {
            htmlOutput += `
              <div class="p-4 bg-amber-50/50 rounded-xl border border-amber-200 mb-3 space-y-2">
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-1 pb-2 border-b border-amber-200">
                  <div>
                    <span class="text-xs font-black uppercase text-amber-900">${rep.ticket_number}</span>
                    <span class="text-[10px] text-slate-500 ml-2">Workshop Lab</span>
                  </div>
                  <span class="text-xs font-bold px-2.5 py-0.5 rounded-full ${getRepairBadgeClass(rep.status)} self-start sm:self-auto">
                    ${rep.status.replace("_", " ").toUpperCase()}
                  </span>
                </div>
                <div class="text-xs text-slate-700 space-y-1">
                  <div><strong>Device:</strong> ${rep.device_brand} ${rep.device_model}</div>
                  <div><strong>Reported Symptoms:</strong> ${rep.problem_description}</div>
                  ${rep.technician_notes ? `<div class="p-2 bg-white rounded border border-amber-200 text-amber-900 text-[11px]"><strong>Laboratory Report:</strong> ${rep.technician_notes}</div>` : ''}
                  <div class="flex items-center gap-4 text-xs font-bold pt-1">
                    <span>Estimated: PKR ${rep.estimated_cost.toLocaleString()}</span>
                    ${rep.final_cost > 0 ? `<span class="text-emerald-700">Final Bill: PKR ${rep.final_cost.toLocaleString()}</span>` : ''}
                  </div>
                </div>
              </div>
            `;
          });
        }
      }
    } catch (e) {
      // Continue
    }

    if (!foundAny) {
      trackerResults.innerHTML = `
        <div class="p-4 bg-slate-50 rounded-xl border border-slate-200 text-center text-xs text-slate-500">
          No records found matching "<strong>${key}</strong>". Please verify your Order / Ticket Number or contact helpline 0300-9607829.
        </div>
      `;
    } else {
      trackerResults.innerHTML = htmlOutput;
    }

    trackSearchBtn.disabled = false;
    trackSearchBtn.innerHTML = `<i class="fa-solid fa-magnifying-glass mr-2 text-amber-400"></i> Check Progress`;
  }

  function getOrderStatusStep(status) {
    if (status === "delivered") return 4;
    if (status === "shipped") return 3;
    if (status === "processing") return 2;
    return 1;
  }

  function getStatusBadgeClass(status) {
    switch (status) {
      case "delivered": return "bg-emerald-100 text-emerald-800";
      case "shipped": return "bg-blue-100 text-blue-800";
      case "confirmed": return "bg-amber-100 text-amber-800";
      case "cancelled": return "bg-red-100 text-red-800";
      default: return "bg-slate-200 text-slate-800";
    }
  }

  function getRepairBadgeClass(status) {
    switch (status) {
      case "ready_for_pickup": return "bg-emerald-500 text-white";
      case "delivered": return "bg-emerald-100 text-emerald-800";
      case "repairing": return "bg-amber-500 text-white";
      case "diagnosing": return "bg-blue-100 text-blue-800";
      default: return "bg-slate-200 text-slate-800";
    }
  }
});
