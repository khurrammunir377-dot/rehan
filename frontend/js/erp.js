// Rehan Computers - Business ERP & POS Management System Logic
if (!window.getProductFallbackImage) {
  window.getProductFallbackImage = function(category = "", brand = "REHAN", title = "") {
    const cat = (category || "").toLowerCase();
    const br = (brand || "REHAN").toUpperCase();
    let icon = "💻";
    let bgGradient = "#0f172a, #1e293b";
    if (cat.includes("gaming")) icon = "🎮", bgGradient = "#1e1b4b, #312e81";
    else if (cat.includes("desktop") || cat.includes("cpu")) icon = "🖥️", bgGradient = "#042f2e, #134e4a";
    else if (cat.includes("monitor") || cat.includes("display") || cat.includes("led")) icon = "📺", bgGradient = "#172554, #1e40af";
    else if (cat.includes("repair")) icon = "🔧", bgGradient = "#451a03, #78350f";
    else if (cat.includes("accessory") || cat.includes("mouse") || cat.includes("keyboard") || cat.includes("ssd") || cat.includes("charger")) icon = "⚡", bgGradient = "#3b0764, #581c87";
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100"><rect width="100" height="100" fill="#0f172a"/><text x="50" y="55" font-size="40" text-anchor="middle" dominant-baseline="middle">${icon}</text></svg>`;
    return "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
  };
}

document.addEventListener("DOMContentLoaded", () => {
  // Authentication State
  let token = localStorage.getItem("rehan_token");
  let currentUser = JSON.parse(localStorage.getItem("rehan_user") || "null");

  // DOM Elements - Auth
  const loginOverlay = document.getElementById("loginOverlay");
  const loginForm = document.getElementById("loginForm");
  const loginUsername = document.getElementById("loginUsername");
  const loginPassword = document.getElementById("loginPassword");
  const loginErrorMsg = document.getElementById("loginErrorMsg");
  const erpUserName = document.getElementById("erpUserName");
  const erpUserRole = document.getElementById("erpUserRole");
  const userAvatar = document.getElementById("userAvatar");
  const logoutBtn = document.getElementById("logoutBtn");
  const pageTitle = document.getElementById("pageTitle");

  // Navigation Tabs
  const navButtons = document.querySelectorAll(".erp-nav-btn");
  const tabPanes = document.querySelectorAll(".erp-tab-pane");

  // State Caches
  let posCart = [];
  let posProducts = [];
  let selectedPayMethod = "cash";
  let selectedPosCategory = "";
  let lastCompletedSale = null;

  // Initialize
  init();

  async function init() {
    setupAuth();
    setupNavigation();
    setupPOS();
    setupModals();

    if (token && currentUser) {
      updateUserHeader();
      hideLogin();
      loadCurrentTab("tab-dashboard");
    } else {
      showLogin();
    }
  }

  // 1. Auth Setup
  function setupAuth() {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      loginErrorMsg.classList.add("hidden");

      const payload = {
        username_or_email: loginUsername.value.trim(),
        password: loginPassword.value.trim()
      };

      const btn = document.getElementById("loginBtn");
      btn.disabled = true;
      btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin mr-2"></i> Authenticating...`;

      try {
        const res = await fetch("/api/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (!res.ok) throw new Error(data.detail || "Login failed");

        token = data.access_token;
        currentUser = data.user;
        localStorage.setItem("rehan_token", token);
        localStorage.setItem("rehan_user", JSON.stringify(currentUser));

        updateUserHeader();
        hideLogin();
        loadCurrentTab("tab-dashboard");
      } catch (err) {
        loginErrorMsg.textContent = err.message;
        loginErrorMsg.classList.remove("hidden");
      } finally {
        btn.disabled = false;
        btn.innerHTML = `<span>Sign In to ERP Portal</span><i class="fa-solid fa-arrow-right text-amber-400"></i>`;
      }
    });

    logoutBtn.addEventListener("click", () => {
      localStorage.removeItem("rehan_token");
      localStorage.removeItem("rehan_user");
      token = null;
      currentUser = null;
      showLogin();
    });
  }

  function showLogin() {
    loginOverlay.classList.remove("hidden");
  }

  function hideLogin() {
    loginOverlay.classList.add("hidden");
  }

  function updateUserHeader() {
    if (!currentUser) return;
    erpUserName.textContent = currentUser.full_name || currentUser.username;
    erpUserRole.textContent = currentUser.role;
    userAvatar.textContent = (currentUser.full_name || currentUser.username)[0].toUpperCase();
  }

  // API Helper with Auth Header
  async function apiFetch(url, options = {}) {
    const headers = options.headers || {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    options.headers = headers;
    const res = await fetch(url, options);
    if (res.status === 401) {
      showLogin();
      throw new Error("Session expired. Please log in again.");
    }
    return res;
  }

  // 2. Navigation Tabs Setup
  function setupNavigation() {
    const sidebarToggleBtn = document.getElementById("sidebarToggleBtn");
    const erpSidebar = document.getElementById("erpSidebar");
    const sidebarBackdrop = document.getElementById("sidebarBackdrop");
    const closeSidebarBtn = document.getElementById("closeSidebarBtn");

    function openSidebar() {
      if (erpSidebar) erpSidebar.classList.remove("-translate-x-full");
      if (sidebarBackdrop) sidebarBackdrop.classList.remove("hidden");
    }

    function closeSidebar() {
      if (erpSidebar) erpSidebar.classList.add("-translate-x-full");
      if (sidebarBackdrop) sidebarBackdrop.classList.add("hidden");
    }

    if (sidebarToggleBtn) {
      sidebarToggleBtn.addEventListener("click", () => {
        if (window.innerWidth < 768) {
          if (erpSidebar && erpSidebar.classList.contains("-translate-x-full")) {
            openSidebar();
          } else {
            closeSidebar();
          }
        } else {
          // Desktop toggle
          erpSidebar.classList.toggle("w-64");
          erpSidebar.classList.toggle("w-0");
          erpSidebar.classList.toggle("overflow-hidden");
        }
      });
    }

    if (closeSidebarBtn) closeSidebarBtn.addEventListener("click", closeSidebar);
    if (sidebarBackdrop) sidebarBackdrop.addEventListener("click", closeSidebar);

    navButtons.forEach(btn => {
      btn.addEventListener("click", () => {
        const tabId = btn.getAttribute("data-tab");
        switchTab(tabId);
        if (window.innerWidth < 768) {
          closeSidebar();
        }
      });
    });
  }

  function switchTab(tabId) {
    navButtons.forEach(b => {
      b.classList.remove("bg-slate-800", "text-amber-400");
      if (b.getAttribute("data-tab") === tabId) {
        b.classList.add("bg-slate-800", "text-amber-400");
        const titleSpan = b.querySelector("span");
        if (titleSpan) pageTitle.textContent = titleSpan.textContent;
      }
    });

    tabPanes.forEach(p => p.classList.add("hidden"));
    const activePane = document.getElementById(tabId);
    if (activePane) activePane.classList.remove("hidden");

    loadCurrentTab(tabId);
  }

  function loadCurrentTab(tabId) {
    if (tabId === "tab-dashboard") loadDashboard();
    else if (tabId === "tab-pos") loadPOS();
    else if (tabId === "tab-products") loadInventory();
    else if (tabId === "tab-orders") loadOrders();
    else if (tabId === "tab-repairs") loadRepairs();
    else if (tabId === "tab-tradein") loadTradeIns();
    else if (tabId === "tab-finance") loadFinance();
    else if (tabId === "tab-crm") loadCRM();
    else if (tabId === "tab-visitors") loadVisitors();
    else if (tabId === "tab-settings") loadSettings();
  }

  // ==================== TAB 1: DASHBOARD ====================
  async function loadDashboard() {
    try {
      const res = await apiFetch("/api/erp/dashboard/stats");
      const stats = await res.json();

      document.getElementById("statGrossRevenue").textContent = `PKR ${stats.total_gross_revenue.toLocaleString()}`;
      document.getElementById("statTodaySales").textContent = `PKR ${stats.today_sales.toLocaleString()}`;
      document.getElementById("statActiveRepairs").textContent = stats.active_repairs_count;
      document.getElementById("statReadyRepairs").textContent = `${stats.ready_repairs_count} Ready for Pickup`;
      document.getElementById("statTotalStock").textContent = `${stats.total_products_count} Items Listed`;
      document.getElementById("statLowStockAlert").textContent = `${stats.low_stock_count} Low Stock Warnings`;

      // Sidebar badges
      const sidebarOrders = document.getElementById("sidebarNewOrdersBadge");
      if (stats.new_orders_count > 0) {
        sidebarOrders.textContent = stats.new_orders_count;
        sidebarOrders.classList.remove("hidden");
      } else {
        sidebarOrders.classList.add("hidden");
      }

      const sidebarRepairs = document.getElementById("sidebarActiveRepairsBadge");
      if (stats.active_repairs_count > 0) {
        sidebarRepairs.textContent = stats.active_repairs_count;
        sidebarRepairs.classList.remove("hidden");
      } else {
        sidebarRepairs.classList.add("hidden");
      }

      // Recent Orders list
      const ordersContainer = document.getElementById("dashRecentOrders");
      if (stats.recent_orders && stats.recent_orders.length > 0) {
        ordersContainer.innerHTML = stats.recent_orders.map(o => `
          <div class="py-2.5 flex items-center justify-between text-xs">
            <div>
              <span class="font-bold text-slate-800">${o.order_number}</span>
              <span class="text-slate-400 ml-2">${o.customer_name}</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="font-black text-brand-900">PKR ${o.total_amount.toLocaleString()}</span>
              <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${o.order_status === 'delivered' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}">
                ${o.order_status}
              </span>
            </div>
          </div>
        `).join("");
      } else {
        ordersContainer.innerHTML = `<p class="py-4 text-xs text-slate-400 text-center">No recent orders</p>`;
      }

      // Recent Repairs list
      const repairsContainer = document.getElementById("dashRecentRepairs");
      if (stats.recent_repairs && stats.recent_repairs.length > 0) {
        repairsContainer.innerHTML = stats.recent_repairs.map(r => `
          <div class="py-2.5 flex items-center justify-between text-xs">
            <div>
              <span class="font-bold text-purple-900">${r.ticket_number}</span>
              <span class="text-slate-500 ml-1">(${r.device_brand} ${r.device_model})</span>
            </div>
            <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${r.status === 'ready_for_pickup' ? 'bg-emerald-500 text-white' : 'bg-purple-100 text-purple-800'}">
              ${r.status.replace("_", " ")}
            </span>
          </div>
        `).join("");
      } else {
        repairsContainer.innerHTML = `<p class="py-4 text-xs text-slate-400 text-center">No active repair tickets</p>`;
      }

      // Activity logs
      const logsContainer = document.getElementById("dashActivityLogs");
      if (stats.recent_logs && stats.recent_logs.length > 0) {
        logsContainer.innerHTML = stats.recent_logs.map(l => `
          <div class="py-2 flex items-start gap-2">
            <span class="font-mono text-slate-400 text-[10px] mt-0.5">${new Date(l.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
            <div>
              <strong class="text-slate-800">${l.username}:</strong> <span>${l.action} — ${l.details}</span>
            </div>
          </div>
        `).join("");
      }
    } catch (err) {
      console.error("Dashboard error", err);
    }
  }

  // ==================== TAB 2: POINT OF SALE (POS) ====================
  function setupPOS() {
    const posSearchInput = document.getElementById("posSearchInput");
    const posClearSearch = document.getElementById("posClearSearch");
    const posDiscount = document.getElementById("posDiscount");
    const posPaidAmount = document.getElementById("posPaidAmount");
    const posResetCartBtn = document.getElementById("posResetCartBtn");
    const posCompleteSaleBtn = document.getElementById("posCompleteSaleBtn");

    let timer;
    posSearchInput.addEventListener("input", () => {
      clearTimeout(timer);
      timer = setTimeout(() => searchPOSProducts(posSearchInput.value.trim(), selectedPosCategory), 300);
    });

    posClearSearch.addEventListener("click", () => {
      posSearchInput.value = "";
      searchPOSProducts("", selectedPosCategory);
    });

    // Sub-category filters (All Items, Laptops, CPU / Desktops, LED / Monitors, Accessories, Storage & RAM)
    document.querySelectorAll(".pos-cat-filter").forEach(btn => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".pos-cat-filter").forEach(b => {
          b.classList.remove("bg-slate-900", "text-white");
          b.classList.add("bg-slate-100", "text-slate-700");
        });
        btn.classList.add("bg-slate-900", "text-white");
        btn.classList.remove("bg-slate-100", "text-slate-700");

        selectedPosCategory = btn.getAttribute("data-cat") || "";
        const q = posSearchInput ? posSearchInput.value.trim() : "";
        searchPOSProducts(q, selectedPosCategory);
      });
    });

    posDiscount.addEventListener("input", updatePOSCartTotals);
    posPaidAmount.addEventListener("input", updatePOSCartTotals);

    posResetCartBtn.addEventListener("click", () => {
      posCart = [];
      updatePOSCartUI();
    });

    // Payment method selector
    document.querySelectorAll(".pos-pay-method").forEach(btn => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".pos-pay-method").forEach(b => {
          b.classList.remove("bg-emerald-600", "text-white");
          b.classList.add("bg-slate-100", "text-slate-700");
        });
        btn.classList.add("bg-emerald-600", "text-white");
        btn.classList.remove("bg-slate-100", "text-slate-700");
        selectedPayMethod = btn.getAttribute("data-pay");
      });
    });

    posCompleteSaleBtn.addEventListener("click", () => completePOSSale(false));

    const posCompleteAndWhatsappBtn = document.getElementById("posCompleteAndWhatsappBtn");
    if (posCompleteAndWhatsappBtn) {
      posCompleteAndWhatsappBtn.addEventListener("click", () => completePOSSale(true));
    }

    // Print Receipt button
    document.getElementById("printNowBtn").addEventListener("click", () => {
      window.print();
    });
    document.getElementById("closeReceiptModal").addEventListener("click", () => {
      document.getElementById("receiptModal").classList.add("hidden");
    });
  }

  async function loadPOS() {
    await searchPOSProducts("", selectedPosCategory);
  }

  async function searchPOSProducts(q = "", category = selectedPosCategory) {
    try {
      const url = `/api/erp/pos/search?q=${encodeURIComponent(q)}&category=${encodeURIComponent(category || "")}`;
      const res = await apiFetch(url);
      posProducts = await res.json();
      renderPOSProducts();
    } catch (err) {
      console.error("POS search error", err);
    }
  }

  function renderPOSProducts() {
    const container = document.getElementById("posProductGrid");
    if (!posProducts || posProducts.length === 0) {
      container.innerHTML = `<p class="col-span-full py-8 text-center text-xs text-slate-400">No matching products found.</p>`;
      return;
    }

    container.innerHTML = posProducts.map(p => {
      const price = p.discount_price && p.discount_price > 0 ? p.discount_price : p.selling_price;
      return `
        <div class="pos-item-card bg-slate-50 hover:bg-brand-50/50 p-2.5 rounded-xl border border-slate-200 cursor-pointer transition flex flex-col justify-between" data-id="${p.id}">
          <div>
            <div class="flex items-center justify-between text-[10px] text-slate-400 mb-1">
              <span class="font-mono">${p.sku}</span>
              <span class="font-bold text-emerald-700 bg-emerald-100 px-1.5 py-0.2 rounded">${p.stock_quantity} left</span>
            </div>
            <h4 class="text-xs font-bold text-slate-900 line-clamp-2">${p.title}</h4>
          </div>
          <div class="pt-2 flex items-baseline justify-between border-t border-slate-200/60 mt-2">
            <span class="text-xs font-black text-brand-950">PKR ${price.toLocaleString()}</span>
            <button class="bg-brand-900 text-white w-6 h-6 rounded flex items-center justify-center text-xs hover:bg-brand-800 shadow">
              <i class="fa-solid fa-plus"></i>
            </button>
          </div>
        </div>
      `;
    }).join("");

    container.querySelectorAll(".pos-item-card").forEach(el => {
      el.addEventListener("click", () => {
        const id = parseInt(el.getAttribute("data-id"));
        const product = posProducts.find(p => p.id === id);
        if (product) addToPOSCart(product);
      });
    });
  }

  function addToPOSCart(product) {
    const existing = posCart.find(it => it.product_id === product.id);
    const price = product.discount_price && product.discount_price > 0 ? product.discount_price : product.selling_price;

    if (existing) {
      if (existing.quantity < product.stock_quantity) {
        existing.quantity += 1;
      } else {
        alert(`Cannot add more. Max stock available: ${product.stock_quantity}`);
      }
    } else {
      posCart.push({
        product_id: product.id,
        title: product.title,
        sku: product.sku,
        unit_price: price,
        quantity: 1,
        serial_number: ""
      });
    }
    updatePOSCartUI();
  }

  function updatePOSCartUI() {
    const container = document.getElementById("posCartList");
    if (posCart.length === 0) {
      container.innerHTML = `<div class="py-8 text-center text-xs text-slate-400">No items scanned yet</div>`;
      updatePOSCartTotals();
      return;
    }

    container.innerHTML = posCart.map((it, idx) => `
      <div class="py-2.5 flex items-center justify-between gap-2">
        <div class="flex-1 min-w-0">
          <div class="font-bold text-slate-900 truncate text-xs">${it.title}</div>
          <div class="flex items-center gap-2 mt-1">
            <span class="font-bold text-brand-900 text-[11px]">PKR ${(it.unit_price * it.quantity).toLocaleString()}</span>
            <input type="text" placeholder="Serial / IMEI" value="${it.serial_number || ''}" class="pos-item-serial bg-white border border-slate-200 rounded px-1.5 py-0.5 text-[10px] w-28" data-idx="${idx}">
          </div>
        </div>
        <div class="flex items-center gap-1.5">
          <button class="pos-qty-minus w-5 h-5 bg-slate-100 rounded text-slate-700 font-bold text-xs" data-idx="${idx}">-</button>
          <span class="text-xs font-bold text-slate-900 w-4 text-center">${it.quantity}</span>
          <button class="pos-qty-plus w-5 h-5 bg-slate-100 rounded text-slate-700 font-bold text-xs" data-idx="${idx}">+</button>
          <button class="pos-item-del text-slate-300 hover:text-red-600 p-1 ml-1" data-idx="${idx}"><i class="fa-solid fa-xmark"></i></button>
        </div>
      </div>
    `).join("");

    container.querySelectorAll(".pos-qty-minus").forEach(b => {
      b.onclick = () => {
        const idx = parseInt(b.getAttribute("data-idx"));
        if (posCart[idx].quantity > 1) posCart[idx].quantity -= 1;
        else posCart.splice(idx, 1);
        updatePOSCartUI();
      };
    });

    container.querySelectorAll(".pos-qty-plus").forEach(b => {
      b.onclick = () => {
        const idx = parseInt(b.getAttribute("data-idx"));
        posCart[idx].quantity += 1;
        updatePOSCartUI();
      };
    });

    container.querySelectorAll(".pos-item-del").forEach(b => {
      b.onclick = () => {
        const idx = parseInt(b.getAttribute("data-idx"));
        posCart.splice(idx, 1);
        updatePOSCartUI();
      };
    });

    container.querySelectorAll(".pos-item-serial").forEach(inp => {
      inp.onchange = () => {
        const idx = parseInt(inp.getAttribute("data-idx"));
        posCart[idx].serial_number = inp.value.trim();
      };
    });

    updatePOSCartTotals();
  }

  function updatePOSCartTotals() {
    const subtotal = posCart.reduce((sum, it) => sum + (it.unit_price * it.quantity), 0);
    const discount = parseFloat(document.getElementById("posDiscount").value) || 0;
    const grandTotal = Math.max(0, subtotal - discount);

    document.getElementById("posSubtotal").textContent = `PKR ${subtotal.toLocaleString()}`;
    document.getElementById("posGrandTotal").textContent = `PKR ${grandTotal.toLocaleString()}`;

    const paidInp = document.getElementById("posPaidAmount");
    const paid = parseFloat(paidInp.value) || 0;
    const change = Math.max(0, paid - grandTotal);
    document.getElementById("posChangeDue").textContent = `PKR ${change.toLocaleString()}`;
  }

  async function completePOSSale(sendToWhatsApp = false) {
    if (posCart.length === 0) {
      alert("Please add at least one product to the POS bill");
      return;
    }

    const subtotal = posCart.reduce((sum, it) => sum + (it.unit_price * it.quantity), 0);
    const discount = parseFloat(document.getElementById("posDiscount").value) || 0;
    const grandTotal = Math.max(0, subtotal - discount);
    const paidInput = document.getElementById("posPaidAmount");
    const amountPaid = parseFloat(paidInput.value) || grandTotal;

    const custName = document.getElementById("posCustomerName").value.trim() || "Walk-in Customer";
    const custPhone = document.getElementById("posCustomerPhone").value.trim() || null;

    const payload = {
      customer_name: custName,
      customer_phone: custPhone,
      payment_method: selectedPayMethod,
      discount: discount,
      tax: 0,
      amount_paid: amountPaid,
      items: posCart.map(it => ({
        product_id: it.product_id,
        quantity: it.quantity,
        unit_price: it.unit_price,
        serial_number: it.serial_number || null
      }))
    };

    const btn = document.getElementById("posCompleteSaleBtn");
    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin mr-2"></i> Generating Invoice...`;

    try {
      const res = await apiFetch("/api/erp/pos/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Checkout failed");

      lastCompletedSale = data;

      // Generate printable thermal receipt preview
      renderThermalReceipt(data);

      // Reset POS cart
      posCart = [];
      document.getElementById("posCustomerName").value = "Walk-in Customer";
      document.getElementById("posCustomerPhone").value = "";
      document.getElementById("posDiscount").value = "0";
      document.getElementById("posPaidAmount").value = "";
      updatePOSCartUI();

      // Show receipt modal
      document.getElementById("receiptModal").classList.remove("hidden");

      if (sendToWhatsApp) {
        let phone = data.customer_phone;
        if (!phone || phone.trim().length < 8) {
          phone = prompt("Enter customer WhatsApp number (e.g. 03009607829):", "");
        }
        if (phone) {
          const waUrl = generateWhatsAppBillUrl(data, phone);
          window.open(waUrl, "_blank");
        } else {
          const waUrl = generateWhatsAppBillUrl(data, "");
          window.open(waUrl, "_blank");
        }
      }
    } catch (err) {
      alert("Error completing sale: " + err.message);
    } finally {
      btn.disabled = false;
      btn.innerHTML = `<i class="fa-solid fa-print"></i> Complete & Print Receipt`;
    }
  }

  function generateWhatsAppBillUrl(sale, targetPhone = null) {
    let phone = (targetPhone || sale.customer_phone || "").trim();
    phone = phone.replace(/[^0-9]/g, "");
    if (phone.startsWith("0")) {
      phone = "92" + phone.substring(1);
    } else if (phone.length === 10 && !phone.startsWith("92")) {
      phone = "92" + phone;
    }

    const itemsSummary = (sale.items || []).map((it, idx) => {
      let line = `${idx + 1}. *${it.product_title}*`;
      if (it.serial_number) line += `\n   S/N: ${it.serial_number}`;
      line += `\n   Qty: ${it.quantity} × PKR ${it.unit_price.toLocaleString()} = *PKR ${it.total_price.toLocaleString()}*`;
      return line;
    }).join("\n\n");

    const message = 
`🧾 *REHAN LAPTOP & COMPUTER — CASH RECEIPT*
📍 Shop #96, 1st Floor, Trust Plaza, Sargodha
📞 0300-9607829 | 🌐 rehancomputers.pk
━━━━━━━━━━━━━━━━━━━━━━━━
*Invoice #:* ${sale.invoice_number}
*Date:* ${new Date().toLocaleDateString('en-GB', {day:'numeric', month:'short', year:'numeric', hour:'2-digit', minute:'2-digit'})}
*Customer:* ${sale.customer_name || 'Walk-in Customer'}
*Cashier:* ${sale.cashier_name || 'Muhammad Rehan'}
━━━━━━━━━━━━━━━━━━━━━━━━
*ITEMS PURCHASED:*
${itemsSummary}
━━━━━━━━━━━━━━━━━━━━━━━━
*Subtotal:* PKR ${sale.subtotal.toLocaleString()}
${sale.discount > 0 ? `*Discount:* - PKR ${sale.discount.toLocaleString()}\n` : ''}*Net Payable:* *PKR ${sale.total_amount.toLocaleString()}*
*Payment Mode:* ${(sale.payment_method || 'CASH').toUpperCase()}
*Paid Amount:* PKR ${sale.amount_paid.toLocaleString()}
*Change Returned:* PKR ${sale.change_returned.toLocaleString()}
━━━━━━━━━━━━━━━━━━━━━━━━
🛡️ *CHECKING WARRANTY:*
• 1-Month Checking Warranty covers internal hardware modules.
• Burnt or physically damaged parts void warranty.

🙏 _Thank you for shopping at Rehan Laptop & Computer Sargodha!_`;

    if (phone && phone.length >= 10) {
      return `https://wa.me/${phone}?text=${encodeURIComponent(message)}`;
    } else {
      return `https://wa.me/?text=${encodeURIComponent(message)}`;
    }
  }

  function renderThermalReceipt(sale) {
    lastCompletedSale = sale;
    const area = document.getElementById("printableReceiptArea");
    const itemRows = sale.items.map(it => `
      <tr>
        <td style="padding: 2px 0;">
          <strong>${it.product_title}</strong>
          ${it.serial_number ? `<br><small>S/N: ${it.serial_number}</small>` : ''}
        </td>
        <td style="text-align: center; padding: 2px 0;">${it.quantity}</td>
        <td style="text-align: right; padding: 2px 0;">${it.total_price.toLocaleString()}</td>
      </tr>
    `).join("");

    area.innerHTML = `
      <div class="thermal-receipt text-center" style="font-family: monospace; font-size: 11px;">
        <h2 style="font-size: 14px; font-weight: bold; margin: 0;">REHAN LAPTOP & COMPUTER</h2>
        <div style="font-size: 10px; margin-top: 2px;">Shop #96, 1st Floor, Trust Plaza, Sargodha</div>
        <div style="font-size: 10px;">Phone & WhatsApp: 0300-9607829</div>
        <hr style="border-top: 1px dashed #000; margin: 6px 0;">
        
        <div style="display: flex; justify-content: space-between; font-size: 10px; text-align: left;">
          <span>Inv: <strong>${sale.invoice_number}</strong></span>
          <span>${new Date().toLocaleDateString()}</span>
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 10px; text-align: left;">
          <span>Cust: ${sale.customer_name || 'Walk-in'}</span>
          <span>Cashier: ${sale.cashier_name || 'Ali Raza'}</span>
        </div>
        <hr style="border-top: 1px dashed #000; margin: 6px 0;">

        <table style="width: 100%; font-size: 10px; text-align: left; border-collapse: collapse;">
          <thead>
            <tr style="border-bottom: 1px solid #000;">
              <th>Item</th>
              <th style="text-align: center;">Qty</th>
              <th style="text-align: right;">Total</th>
            </tr>
          </thead>
          <tbody>
            ${itemRows}
          </tbody>
        </table>

        <hr style="border-top: 1px dashed #000; margin: 6px 0;">
        <div style="display: flex; justify-content: space-between; font-size: 11px;">
          <span>Subtotal:</span>
          <span>PKR ${sale.subtotal.toLocaleString()}</span>
        </div>
        ${sale.discount > 0 ? `
          <div style="display: flex; justify-content: space-between; font-size: 11px;">
            <span>Discount:</span>
            <span>- PKR ${sale.discount.toLocaleString()}</span>
          </div>
        ` : ''}
        <div style="display: flex; justify-content: space-between; font-size: 12px; font-weight: bold; margin-top: 2px;">
          <span>Net Payable:</span>
          <span>PKR ${sale.total_amount.toLocaleString()}</span>
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 10px; margin-top: 2px;">
          <span>Paid (${sale.payment_method}):</span>
          <span>PKR ${sale.amount_paid.toLocaleString()}</span>
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 10px;">
          <span>Change Returned:</span>
          <span>PKR ${sale.change_returned.toLocaleString()}</span>
        </div>

        <hr style="border-top: 1px dashed #000; margin: 8px 0;">
        <div style="font-size: 9px; line-height: 1.3;">
          * 1-Month Checking Warranty covers hardware faults.<br>
          * No warranty on burnt or broken parts.<br>
          * Thank you for shopping with Rehan Computers Sargodha!
        </div>
      </div>
    `;

    // Hook up WhatsApp Bill button in receipt modal
    const waBtn = document.getElementById("posSendWhatsappBtn");
    if (waBtn) {
      waBtn.onclick = (e) => {
        e.preventDefault();
        let phone = sale.customer_phone;
        if (!phone || phone.trim().length < 8) {
          phone = prompt("Enter customer WhatsApp number (e.g. 03009607829):", "");
        }
        if (phone) {
          const waUrl = generateWhatsAppBillUrl(sale, phone);
          window.open(waUrl, "_blank");
        } else {
          const waUrl = generateWhatsAppBillUrl(sale, "");
          window.open(waUrl, "_blank");
        }
      };
    }
  }

  // ==================== TAB 3: INVENTORY ====================
  async function loadInventory() {
    try {
      const res = await apiFetch("/api/erp/products");
      const products = await res.json();
      renderInventoryTable(products);
    } catch (err) {
      console.error("Inventory error", err);
    }
  }

  function renderInventoryTable(products) {
    const tbody = document.getElementById("inventoryTableBody");
    if (!products || products.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="py-8 text-center text-slate-400">No products found.</td></tr>`;
      return;
    }

    tbody.innerHTML = products.map(p => `
      <tr class="hover:bg-slate-50 transition">
        <td class="py-3 px-4">
          <div class="flex items-center gap-3">
            <img 
              src="${p.image_url || window.getProductFallbackImage(p.category_name, p.brand_name, p.title)}" 
              onerror="this.onerror=null; this.src=window.getProductFallbackImage('${(p.category_name || '').replace(/['\"]/g, '')}', '${(p.brand_name || '').replace(/['\"]/g, '')}', '${(p.title || '').replace(/['\"]/g, '')}');"
              class="w-10 h-10 rounded-lg object-cover bg-slate-100 border border-slate-200"
            >
            <div>
              <div class="font-bold text-slate-900">${p.title}</div>
              <div class="text-[10px] text-slate-400 font-mono">${p.sku} | ${p.brand_name || 'Generic'}</div>
            </div>
          </div>
        </td>
        <td class="py-3 px-4">
          <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${p.condition === 'Brand New' ? 'bg-emerald-100 text-emerald-800' : 'bg-blue-100 text-blue-800'}">
            ${p.condition}
          </span>
        </td>
        <td class="py-3 px-4 font-mono">${p.cost_price.toLocaleString()}</td>
        <td class="py-3 px-4 font-black text-brand-900">${p.selling_price.toLocaleString()}</td>
        <td class="py-3 px-4">
          <span class="font-bold ${p.stock_quantity <= p.min_stock_alert ? 'text-amber-600 bg-amber-50 px-2 py-0.5 rounded' : 'text-slate-800'}">
            ${p.stock_quantity}
          </span>
        </td>
        <td class="py-3 px-4 text-slate-500">${p.available_serials_count || 0}</td>
        <td class="py-3 px-4 text-right flex items-center justify-end gap-1.5">
          <button 
            class="inv-price-pic-btn text-xs font-bold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 px-2.5 py-1 rounded-lg border border-emerald-200 transition" 
            data-id="${p.id}" 
            data-title="${(p.title || '').replace(/"/g, '&quot;')}" 
            data-sku="${p.sku || ''}" 
            data-cost="${p.cost_price || 0}" 
            data-price="${p.selling_price || 0}" 
            data-discount="${p.discount_price || ''}" 
            data-img="${p.image_url || ''}"
          >
            <i class="fa-solid fa-camera mr-1"></i> Price & Pic
          </button>
          <button class="inv-adjust-btn text-xs font-bold text-brand-700 hover:bg-brand-50 px-2 py-1 rounded" data-id="${p.id}" data-title="${(p.title || '').replace(/"/g, '&quot;')}">
            <i class="fa-solid fa-plus-minus mr-1"></i> Stock
          </button>
        </td>
      </tr>
    `).join("");

    tbody.querySelectorAll(".inv-price-pic-btn").forEach(btn => {
      btn.onclick = () => {
        const id = btn.getAttribute("data-id");
        const title = btn.getAttribute("data-title");
        const sku = btn.getAttribute("data-sku");
        const cost = btn.getAttribute("data-cost");
        const price = btn.getAttribute("data-price");
        const discount = btn.getAttribute("data-discount");
        const img = btn.getAttribute("data-img");

        document.getElementById("editProdId").value = id;
        document.getElementById("editPricePicSubtitle").textContent = `${title} (${sku})`;
        document.getElementById("editSellingPrice").value = price;
        document.getElementById("editCostPrice").value = cost;
        document.getElementById("editDiscountPrice").value = discount;
        document.getElementById("editPicUrl").value = img;
        document.getElementById("editPicPreview").src = img || 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" fill="%23cbd5e1" viewBox="0 0 24 24"><path d="M4 5h16a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2zm0 2v10h16V7H4zm3 2a2 2 0 1 0 0 4 2 2 0 0 0 0-4zm11 7l-4.5-6-3.5 4.5-2.5-3-3.5 4.5h14z"/></svg>';
        
        const uploadStatus = document.getElementById("uploadStatusText");
        if (uploadStatus) {
          uploadStatus.textContent = "JPG, PNG, WebP";
          uploadStatus.className = "text-[10px] text-slate-500";
        }
        document.getElementById("editPricePicModal").classList.remove("hidden");
      };
    });

    tbody.querySelectorAll(".inv-adjust-btn").forEach(btn => {
      btn.onclick = async () => {
        const id = btn.getAttribute("data-id");
        const title = btn.getAttribute("data-title");
        const changeStr = prompt(`Adjust stock for: ${title}\nEnter quantity change (e.g. +5 or -2):`, "+1");
        if (!changeStr) return;
        const change = parseInt(changeStr);
        if (isNaN(change)) return alert("Invalid number");

        const reason = prompt("Enter reason for stock adjustment:", "Restock / Sold on counter") || "Manual adjustment";
        try {
          await apiFetch(`/api/erp/products/${id}/adjust-stock`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ quantity_change: change, reason: reason })
          });
          loadInventory();
        } catch (err) {
          alert("Adjustment failed: " + err.message);
        }
      };
    });
  }

  // ==================== TAB 4: ORDERS ====================
  async function loadOrders() {
    try {
      const res = await apiFetch("/api/erp/orders");
      const orders = await res.json();
      document.getElementById("ordersListCount").textContent = `${orders.length} total orders`;
      renderOrdersTable(orders);
    } catch (err) {
      console.error("Orders error", err);
    }
  }

  function renderOrdersTable(orders) {
    const tbody = document.getElementById("ordersTableBody");
    if (!orders || orders.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="py-8 text-center text-slate-400">No orders recorded yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = orders.map(o => `
      <tr class="hover:bg-slate-50 transition">
        <td class="py-3 px-4 font-mono font-bold text-brand-900">${o.order_number}</td>
        <td class="py-3 px-4">
          <div class="font-bold text-slate-900">${o.customer_name}</div>
          <div class="text-[10px] text-slate-400">${o.customer_phone}</div>
        </td>
        <td class="py-3 px-4 text-slate-600 max-w-xs truncate">${o.shipping_address}, ${o.city}</td>
        <td class="py-3 px-4 font-black">PKR ${o.total_amount.toLocaleString()}</td>
        <td class="py-3 px-4">
          <select class="order-status-select bg-slate-50 border border-slate-300 rounded px-2 py-1 text-[11px] font-bold" data-id="${o.id}">
            <option value="new" ${o.order_status === 'new' ? 'selected' : ''}>New</option>
            <option value="confirmed" ${o.order_status === 'confirmed' ? 'selected' : ''}>Confirmed</option>
            <option value="processing" ${o.order_status === 'processing' ? 'selected' : ''}>Processing</option>
            <option value="shipped" ${o.order_status === 'shipped' ? 'selected' : ''}>Shipped</option>
            <option value="delivered" ${o.order_status === 'delivered' ? 'selected' : ''}>Delivered</option>
            <option value="cancelled" ${o.order_status === 'cancelled' ? 'selected' : ''}>Cancelled</option>
          </select>
        </td>
        <td class="py-3 px-4 text-[11px]">
          <div>${o.courier_name || 'Not assigned'}</div>
          <code class="text-slate-500">${o.courier_tracking_no || ''}</code>
        </td>
        <td class="py-3 px-4 text-right">
          <a 
            href="https://wa.me/${o.customer_phone.replace(/[^0-9]/g, '')}?text=${encodeURIComponent('Assalam-o-Alaikum ' + o.customer_name + '! This is Rehan Computers Sargodha regarding your order ' + o.order_number + '. Status: ' + o.order_status + '. Courier: ' + (o.courier_name || 'Store Rider') + ' Tracking: ' + (o.courier_tracking_no || 'Assigned'))}" 
            target="_blank" 
            class="text-emerald-700 hover:bg-emerald-50 px-2 py-1 rounded text-xs font-bold inline-flex items-center gap-1"
          >
            <i class="fa-brands fa-whatsapp text-sm"></i> WhatsApp
          </a>
        </td>
      </tr>
    `).join("");

    tbody.querySelectorAll(".order-status-select").forEach(sel => {
      sel.onchange = async () => {
        const id = sel.getAttribute("data-id");
        const newStatus = sel.value;
        let courier = null;
        let tracking = null;

        if (newStatus === "shipped") {
          courier = prompt("Enter Courier Name (e.g. TCS Express, Leopards, Trax):", "TCS Express");
          tracking = prompt("Enter Courier Consignment / Tracking #:", "TCS-");
        }

        try {
          await apiFetch(`/api/erp/orders/${id}/status`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              order_status: newStatus,
              courier_name: courier,
              courier_tracking_no: tracking,
              payment_status: newStatus === "delivered" ? "paid" : "pending"
            })
          });
          loadOrders();
        } catch (err) {
          alert("Status update failed: " + err.message);
        }
      };
    });
  }

  // ==================== TAB 5: WORKSHOP & REPAIRS ====================
  async function loadRepairs() {
    try {
      const res = await apiFetch("/api/erp/repairs");
      const repairs = await res.json();
      renderRepairsTable(repairs);
    } catch (err) {
      console.error("Repairs error", err);
    }
  }

  function renderRepairsTable(repairs) {
    const tbody = document.getElementById("repairsTableBody");
    if (!repairs || repairs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="py-8 text-center text-slate-400">No repair jobs logged.</td></tr>`;
      return;
    }

    tbody.innerHTML = repairs.map(r => `
      <tr class="hover:bg-slate-50 transition">
        <td class="py-3 px-4 font-mono font-bold text-purple-900">${r.ticket_number}</td>
        <td class="py-3 px-4">
          <div class="font-bold text-slate-900">${r.customer_name}</div>
          <div class="text-[10px] text-slate-400">${r.customer_phone}</div>
        </td>
        <td class="py-3 px-4">
          <div class="font-bold text-slate-800">${r.device_brand} ${r.device_model}</div>
          <div class="text-[10px] text-slate-400">Acc: ${r.accessories_received || 'None'}</div>
        </td>
        <td class="py-3 px-4 text-slate-600 max-w-xs truncate">${r.problem_description}</td>
        <td class="py-3 px-4">
          <select class="repair-status-select bg-slate-50 border border-slate-300 rounded px-2 py-1 text-[11px] font-bold" data-id="${r.id}">
            <option value="received" ${r.status === 'received' ? 'selected' : ''}>Received</option>
            <option value="diagnosing" ${r.status === 'diagnosing' ? 'selected' : ''}>Diagnosing</option>
            <option value="awaiting_parts" ${r.status === 'awaiting_parts' ? 'selected' : ''}>Awaiting Parts</option>
            <option value="repairing" ${r.status === 'repairing' ? 'selected' : ''}>Repairing</option>
            <option value="ready_for_pickup" ${r.status === 'ready_for_pickup' ? 'selected' : ''}>Ready for Pickup</option>
            <option value="delivered" ${r.status === 'delivered' ? 'selected' : ''}>Delivered / Closed</option>
          </select>
        </td>
        <td class="py-3 px-4 font-black">
          ${r.final_cost > 0 ? `PKR ${r.final_cost.toLocaleString()}` : `Est: PKR ${r.estimated_cost.toLocaleString()}`}
        </td>
        <td class="py-3 px-4 text-right">
          <a 
            href="https://wa.me/${r.customer_phone.replace(/[^0-9]/g, '')}?text=${encodeURIComponent('Assalam-o-Alaikum ' + r.customer_name + '! This is Rehan Laptop & Computer, Shop #96 Trust Plaza Sargodha regarding your ' + r.device_brand + ' ' + r.device_model + ' (Ticket ' + r.ticket_number + '). Status: ' + r.status.replace('_', ' ') + '. Total: PKR ' + (r.final_cost || r.estimated_cost).toLocaleString())}" 
            target="_blank" 
            class="text-purple-700 hover:bg-purple-50 px-2 py-1 rounded text-xs font-bold inline-flex items-center gap-1"
          >
            <i class="fa-brands fa-whatsapp text-sm"></i> WhatsApp
          </a>
        </td>
      </tr>
    `).join("");

    tbody.querySelectorAll(".repair-status-select").forEach(sel => {
      sel.onchange = async () => {
        const id = sel.getAttribute("data-id");
        const status = sel.value;
        let finalCost = null;
        let notes = null;

        if (status === "ready_for_pickup") {
          finalCost = parseFloat(prompt("Enter Final Bill Amount for Customer (PKR):", "6500"));
          notes = prompt("Enter Technician Completion Note:", "Motherboard diagnosed and tested OK.");
        }

        try {
          await apiFetch(`/api/erp/repairs/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              status: status,
              final_cost: finalCost,
              technician_notes: notes
            })
          });
          loadRepairs();
        } catch (err) {
          alert("Failed to update repair: " + err.message);
        }
      };
    });
  }

  // ==================== TAB 6: TRADE-IN ====================
  async function loadTradeIns() {
    try {
      const res = await apiFetch("/api/erp/crm/trade-ins");
      const list = await res.json();
      const tbody = document.getElementById("tradeInTableBody");

      if (!list || list.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" class="py-8 text-center text-slate-400">No trade-in submissions.</td></tr>`;
        return;
      }

      tbody.innerHTML = list.map(t => `
        <tr class="hover:bg-slate-50 transition">
          <td class="py-3 px-4 font-mono font-bold text-emerald-900">${t.request_code}</td>
          <td class="py-3 px-4">
            <div class="font-bold text-slate-900">${t.customer_name}</div>
            <div class="text-[10px] text-slate-400">${t.customer_phone}</div>
          </td>
          <td class="py-3 px-4">
            <div class="font-bold">${t.device_brand} ${t.device_model}</div>
            <div class="text-[10px] text-slate-500">${t.specs_details}</div>
          </td>
          <td class="py-3 px-4">${t.condition_grade}</td>
          <td class="py-3 px-4 font-mono">PKR ${(t.customer_expected_price || 0).toLocaleString()}</td>
          <td class="py-3 px-4 font-bold text-emerald-700">PKR ${(t.estimated_offer_price || 0).toLocaleString()}</td>
          <td class="py-3 px-4 font-bold text-xs uppercase">${t.status}</td>
          <td class="py-3 px-4 text-right">
            <button class="trade-offer-btn text-xs font-bold text-brand-900 hover:underline" data-id="${t.id}">Offer Quote</button>
          </td>
        </tr>
      `).join("");

      tbody.querySelectorAll(".trade-offer-btn").forEach(btn => {
        btn.onclick = async () => {
          const id = btn.getAttribute("data-id");
          const offer = parseFloat(prompt("Enter Evaluation Offer (PKR):", "22000"));
          if (isNaN(offer)) return;
          await apiFetch(`/api/erp/crm/trade-ins/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ estimated_offer_price: offer, status: "accepted" })
          });
          loadTradeIns();
        };
      });
    } catch (err) {
      console.error("Trade-in error", err);
    }
  }

  // ==================== TAB 7: FINANCE & EXPENSES ====================
  async function loadFinance() {
    try {
      const resPnl = await apiFetch("/api/erp/finance/profit-loss");
      const pnl = await resPnl.json();

      document.getElementById("financeGrossRev").textContent = `PKR ${pnl.gross_revenue.toLocaleString()}`;
      document.getElementById("financeExpensesTotal").textContent = `PKR ${pnl.total_expenses.toLocaleString()}`;
      document.getElementById("financeNetProfit").textContent = `PKR ${pnl.net_profit.toLocaleString()}`;

      // Expenses Table
      const resExp = await apiFetch("/api/erp/finance/expenses");
      const expenses = await resExp.json();
      const tbody = document.getElementById("expensesTableBody");

      if (!expenses || expenses.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="py-6 text-center text-slate-400">No expenses recorded for this month.</td></tr>`;
        return;
      }

      tbody.innerHTML = expenses.map(e => `
        <tr class="hover:bg-slate-50 transition">
          <td class="py-2.5 px-3 font-mono text-slate-500">${e.expense_date}</td>
          <td class="py-2.5 px-3 font-bold text-slate-800">${e.category}</td>
          <td class="py-2.5 px-3 text-slate-600">${e.description}</td>
          <td class="py-2.5 px-3 capitalize text-slate-500">${e.payment_method}</td>
          <td class="py-2.5 px-3 font-black text-red-700">PKR ${e.amount.toLocaleString()}</td>
          <td class="py-2.5 px-3 text-slate-400 text-[10px]">${e.recorded_by_name || 'Admin'}</td>
        </tr>
      `).join("");
    } catch (err) {
      console.error("Finance error", err);
    }
  }

  // ==================== TAB 8: CRM ====================
  async function loadCRM() {
    try {
      const res = await apiFetch("/api/erp/crm/customers");
      const customers = await res.json();
      const tbody = document.getElementById("customersTableBody");

      if (!customers || customers.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="py-8 text-center text-slate-400">No customers recorded.</td></tr>`;
        return;
      }

      tbody.innerHTML = customers.map(c => `
        <tr class="hover:bg-slate-50 transition">
          <td class="py-3 px-4 font-bold text-slate-900">${c.name}</td>
          <td class="py-3 px-4 font-mono">${c.phone}</td>
          <td class="py-3 px-4">${c.city || 'Sargodha'}</td>
          <td class="py-3 px-4 font-black text-brand-900">PKR ${(c.total_spent || 0).toLocaleString()}</td>
          <td class="py-3 px-4">${c.orders_count || 0}</td>
          <td class="py-3 px-4">${c.repairs_count || 0}</td>
          <td class="py-3 px-4 text-right">
            <a href="https://wa.me/${c.phone.replace(/[^0-9]/g, '')}" target="_blank" class="text-emerald-700 font-bold hover:underline">
              <i class="fa-brands fa-whatsapp mr-1"></i> WhatsApp
            </a>
          </td>
        </tr>
      `).join("");
    } catch (err) {
      console.error("CRM error", err);
    }
  }

  // ==================== TAB 9: VISITORS & TRAFFIC CONTROLS ====================
  async function loadVisitors() {
    try {
      // 1. Fetch Stats & Controls
      const statsRes = await apiFetch("/api/erp/visitors/stats");
      const stats = await statsRes.json();

      const liveEl = document.getElementById("statLiveOnline");
      if (liveEl) liveEl.textContent = stats.active_online_visitors || 1;

      const uniqueEl = document.getElementById("statTodayUnique");
      if (uniqueEl) uniqueEl.textContent = (stats.today_unique_visitors || 0).toLocaleString();

      const hitsEl = document.getElementById("statTodayHits");
      if (hitsEl) hitsEl.textContent = (stats.today_pageviews || 0).toLocaleString();

      const allUniqueEl = document.getElementById("statAllTimeUnique");
      if (allUniqueEl) allUniqueEl.textContent = (stats.total_unique_visitors || 0).toLocaleString();

      const toggleMaintenance = document.getElementById("toggleMaintenance");
      if (toggleMaintenance) {
        toggleMaintenance.checked = !!stats.maintenance_mode;
      }

      // Device breakdown
      const devContainer = document.getElementById("deviceBreakdownList");
      if (devContainer) {
        if (stats.device_breakdown && stats.device_breakdown.length > 0) {
          devContainer.innerHTML = stats.device_breakdown.map(d => `
            <div class="flex items-center justify-between py-1.5 border-b border-slate-100 last:border-0">
              <span class="font-bold text-slate-700 capitalize"><i class="fa-solid fa-laptop text-brand-900 mr-2"></i> ${d.device_type}</span>
              <span class="font-mono bg-slate-100 px-2 py-0.5 rounded text-slate-800 font-black">${d.count} hits</span>
            </div>
          `).join("");
        } else {
          devContainer.innerHTML = `<div class="text-slate-400 text-center py-2">No device traffic recorded yet</div>`;
        }
      }

      // Browser breakdown
      const brContainer = document.getElementById("browserBreakdownList");
      if (brContainer) {
        if (stats.top_browsers && stats.top_browsers.length > 0) {
          brContainer.innerHTML = stats.top_browsers.map(b => `
            <div class="flex items-center justify-between py-1.5 border-b border-slate-100 last:border-0">
              <span class="font-bold text-slate-700"><i class="fa-brands fa-chrome text-amber-500 mr-2"></i> ${b.browser}</span>
              <span class="font-mono bg-slate-100 px-2 py-0.5 rounded text-slate-800 font-black">${b.count} hits</span>
            </div>
          `).join("");
        } else {
          brContainer.innerHTML = `<div class="text-slate-400 text-center py-2">No browser data yet</div>`;
        }
      }

      // Top pages
      const pageContainer = document.getElementById("topPagesList");
      if (pageContainer) {
        if (stats.top_pages && stats.top_pages.length > 0) {
          pageContainer.innerHTML = stats.top_pages.map(p => `
            <div class="flex items-center justify-between py-1.5 border-b border-slate-100 last:border-0">
              <span class="font-mono text-slate-800 truncate max-w-[180px]">${p.page_url}</span>
              <span class="font-mono bg-blue-50 text-blue-700 px-2 py-0.5 rounded font-black">${p.hits} views</span>
            </div>
          `).join("");
        } else {
          pageContainer.innerHTML = `<div class="text-slate-400 text-center py-2">No page data yet</div>`;
        }
      }

      // 2. Fetch Visitor Logs
      const logsRes = await apiFetch("/api/erp/visitors/logs?limit=50");
      const logs = await logsRes.json();
      const logCountEl = document.getElementById("visitorLogCount");
      if (logCountEl) logCountEl.textContent = `${logs.length} sessions`;
      renderVisitorLogsTable(logs);

      // 3. Fetch Blocked IPs
      const blockedRes = await apiFetch("/api/erp/visitors/blocked-ips");
      const blocked = await blockedRes.json();
      renderBlockedIpsTable(blocked);

    } catch (err) {
      console.error("Visitors error", err);
    }
  }

  function renderVisitorLogsTable(logs) {
    const tbody = document.getElementById("visitorsTableBody");
    if (!tbody) return;
    if (!logs || logs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="py-8 text-center text-slate-400">No visitor sessions recorded yet. Browse the storefront to generate traffic!</td></tr>`;
      return;
    }

    tbody.innerHTML = logs.map(l => `
      <tr class="hover:bg-slate-50 transition">
        <td class="py-3 px-4 font-mono font-bold text-slate-900 flex items-center gap-2">
          <span class="w-2 h-2 rounded-full ${l.is_blocked ? 'bg-red-500' : 'bg-emerald-500'}"></span>
          ${l.ip_address}
        </td>
        <td class="py-3 px-4 text-slate-600">${l.city || 'Sargodha'}, ${l.country || 'PK'}</td>
        <td class="py-3 px-4 font-mono text-slate-800 truncate max-w-[160px]">${l.page_url || '/'}</td>
        <td class="py-3 px-4 capitalize text-slate-700">${l.device_type || 'Desktop'} (${l.os || 'Windows'})</td>
        <td class="py-3 px-4 text-slate-700">${l.browser || 'Browser'}</td>
        <td class="py-3 px-4 text-slate-400 font-mono text-[11px]">${new Date(l.created_at || l.timestamp).toLocaleString([], {month:'short', day:'numeric', hour:'2-digit', minute:'2-digit'})}</td>
        <td class="py-3 px-4 text-right">
          ${l.is_blocked ? `
            <span class="text-xs font-bold text-red-600 bg-red-50 px-2 py-1 rounded border border-red-200">
              <i class="fa-solid fa-ban mr-1"></i> Blocked
            </span>
          ` : `
            <button class="block-visitor-ip-btn text-xs font-bold text-red-600 hover:bg-red-50 px-2.5 py-1 rounded-lg border border-red-200 transition" data-ip="${l.ip_address}">
              <i class="fa-solid fa-ban mr-1"></i> Block IP
            </button>
          `}
        </td>
      </tr>
    `).join("");

    tbody.querySelectorAll(".block-visitor-ip-btn").forEach(btn => {
      btn.onclick = async () => {
        const ip = btn.getAttribute("data-ip");
        const reason = prompt(`Block IP Address ${ip} from visiting store?\nEnter reason:`, "Suspicious activity / spam") || "Manual block";
        try {
          await apiFetch("/api/erp/visitors/block-ip", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ip_address: ip, reason: reason })
          });
          alert(`IP address ${ip} has been blocked.`);
          loadVisitors();
        } catch (err) {
          alert("Error blocking IP: " + err.message);
        }
      };
    });
  }

  function renderBlockedIpsTable(blocked) {
    const tbody = document.getElementById("blockedIpsTableBody");
    if (!tbody) return;
    if (!blocked || blocked.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" class="py-6 text-center text-slate-400">No IP addresses currently restricted or banned.</td></tr>`;
      return;
    }

    tbody.innerHTML = blocked.map(b => `
      <tr class="hover:bg-slate-50 transition">
        <td class="py-2.5 px-4 font-mono font-bold text-red-700">${b.ip_address}</td>
        <td class="py-2.5 px-4 text-slate-600">${b.reason || 'Restricted by Admin'}</td>
        <td class="py-2.5 px-4 text-slate-500">${b.blocked_by || 'Admin'}</td>
        <td class="py-2.5 px-4 text-slate-400 font-mono text-[11px]">${new Date(b.created_at).toLocaleString([], {month:'short', day:'numeric', hour:'2-digit', minute:'2-digit'})}</td>
        <td class="py-2.5 px-4 text-right">
          <button class="unblock-visitor-ip-btn text-xs font-bold text-emerald-700 hover:bg-emerald-50 px-2.5 py-1 rounded-lg border border-emerald-200 transition" data-ip="${b.ip_address}">
            <i class="fa-solid fa-unlock mr-1"></i> Unblock IP
          </button>
        </td>
      </tr>
    `).join("");

    tbody.querySelectorAll(".unblock-visitor-ip-btn").forEach(btn => {
      btn.onclick = async () => {
        const ip = btn.getAttribute("data-ip");
        if (!confirm(`Are you sure you want to unblock IP address ${ip}?`)) return;
        try {
          await apiFetch("/api/erp/visitors/unblock-ip", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ip_address: ip })
          });
          alert(`IP address ${ip} unblocked.`);
          loadVisitors();
        } catch (err) {
          alert("Error unblocking IP: " + err.message);
        }
      };
    });
  }

  // ==================== TAB 10: SETTINGS ====================
  async function loadSettings() {
    try {
      const res = await apiFetch("/api/erp/settings");
      const settings = await res.json();

      document.getElementById("setStoreName").value = settings.store_name || "";
      document.getElementById("setPhone").value = settings.phone || "";
      document.getElementById("setAddress").value = settings.address || "";
      document.getElementById("setAddressUr").value = settings.address_ur || "";
      document.getElementById("setReceiptFooter").value = settings.receipt_footer || "";
    } catch (err) {
      console.error("Settings error", err);
    }
  }

  // Modals Setup (Add Product, Add Expense)
  function setupModals() {
    // Add Product Modal
    const addProductModal = document.getElementById("addProductModal");
    const addNewProductBtn = document.getElementById("addNewProductBtn");
    const closeAddProductModal = document.getElementById("closeAddProductModal");
    const addProductForm = document.getElementById("addProductForm");

    if (addNewProductBtn) {
      addNewProductBtn.onclick = async () => {
        // Populate categories & brands
        const catRes = await fetch("/api/public/categories");
        const cats = await catRes.json();
        const brandRes = await fetch("/api/public/brands");
        const brands = await brandRes.json();

        const catSel = document.getElementById("addProdCategory");
        catSel.innerHTML = cats.map(c => `<option value="${c.id}">${c.name}</option>`).join("");

        const brandSel = document.getElementById("addProdBrand");
        brandSel.innerHTML = brands.map(b => `<option value="${b.id}">${b.name}</option>`).join("");

        addProductModal.classList.remove("hidden");
      };
    }

    if (closeAddProductModal) {
      closeAddProductModal.onclick = () => addProductModal.classList.add("hidden");
    }

    addProductForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const payload = {
        title: document.getElementById("addProdTitle").value.trim(),
        brand_id: parseInt(document.getElementById("addProdBrand").value),
        category_id: parseInt(document.getElementById("addProdCategory").value),
        condition: document.getElementById("addProdCondition").value,
        cost_price: parseFloat(document.getElementById("addProdCost").value),
        selling_price: parseFloat(document.getElementById("addProdPrice").value),
        stock_quantity: parseInt(document.getElementById("addProdStock").value) || 1,
        warranty_period: document.getElementById("addProdWarranty").value,
        image_url: document.getElementById("addProdImage").value,
        specs: { details: document.getElementById("addProdSpecs").value }
      };

      try {
        await apiFetch("/api/erp/products", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        addProductForm.reset();
        addProductModal.classList.add("hidden");
        loadInventory();
        alert("Product added to inventory!");
      } catch (err) {
        alert("Error adding product: " + err.message);
      }
    });

    // Add Expense Modal
    const addExpenseModal = document.getElementById("addExpenseModal");
    const addExpenseBtn = document.getElementById("addExpenseBtn");
    const closeAddExpenseModal = document.getElementById("closeAddExpenseModal");
    const recordExpenseForm = document.getElementById("recordExpenseForm");

    if (addExpenseBtn) {
      addExpenseBtn.onclick = () => addExpenseModal.classList.remove("hidden");
    }
    if (closeAddExpenseModal) {
      closeAddExpenseModal.onclick = () => addExpenseModal.classList.add("hidden");
    }

    recordExpenseForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const payload = {
        category: document.getElementById("expCategory").value,
        amount: parseFloat(document.getElementById("expAmount").value),
        description: document.getElementById("expDesc").value.trim()
      };

      try {
        await apiFetch("/api/erp/finance/expenses", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        recordExpenseForm.reset();
        addExpenseModal.classList.add("hidden");
        loadFinance();
        alert("Expense recorded!");
      } catch (err) {
        alert("Error: " + err.message);
      }
    });

    // Store Settings Save Form
    const storeSettingsForm = document.getElementById("storeSettingsForm");
    if (storeSettingsForm) {
      storeSettingsForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const payload = {
          store_name: document.getElementById("setStoreName").value.trim(),
          phone: document.getElementById("setPhone").value.trim(),
          address: document.getElementById("setAddress").value.trim(),
          address_ur: document.getElementById("setAddressUr").value.trim(),
          receipt_footer: document.getElementById("setReceiptFooter").value.trim()
        };

        try {
          await apiFetch("/api/erp/settings", {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
          });
          alert("Store settings updated successfully!");
        } catch (err) {
          alert("Error: " + err.message);
        }
      });
    }

    // Dedicated Edit Price & Pictures Modal
    const editPricePicModal = document.getElementById("editPricePicModal");
    const closeEditPricePicModal = document.getElementById("closeEditPricePicModal");
    const editPricePicForm = document.getElementById("editPricePicForm");
    const editPicFileInput = document.getElementById("editPicFileInput");
    const editPicUrl = document.getElementById("editPicUrl");
    const editPicPreview = document.getElementById("editPicPreview");
    const uploadStatusText = document.getElementById("uploadStatusText");

    if (closeEditPricePicModal) {
      closeEditPricePicModal.onclick = () => editPricePicModal.classList.add("hidden");
    }

    if (editPicUrl) {
      editPicUrl.addEventListener("input", () => {
        const url = editPicUrl.value.trim();
        if (url) {
          editPicPreview.src = url;
        }
      });
    }

    if (editPicFileInput) {
      editPicFileInput.addEventListener("change", (e) => {
        const file = e.target.files[0];
        if (!file) return;

        if (file.size > 8 * 1024 * 1024) {
          alert("File size exceeds 8MB limit. Please choose a smaller image.");
          return;
        }

        uploadStatusText.textContent = "Uploading image...";
        uploadStatusText.className = "text-[10px] text-amber-600 font-bold";

        const reader = new FileReader();
        reader.onload = async () => {
          try {
            const res = await apiFetch("/api/erp/products/upload-image", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                filename: file.name,
                data_base64: reader.result
              })
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "Upload failed");

            editPicUrl.value = data.url;
            editPicPreview.src = data.url;
            uploadStatusText.textContent = "Photo uploaded successfully!";
            uploadStatusText.className = "text-[10px] text-emerald-600 font-bold";
          } catch (err) {
            uploadStatusText.textContent = "Upload failed: " + err.message;
            uploadStatusText.className = "text-[10px] text-red-600 font-bold";
          }
        };
        reader.readAsDataURL(file);
      });
    }

    if (editPricePicForm) {
      editPricePicForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const prodId = document.getElementById("editProdId").value;
        const sellingPrice = parseFloat(document.getElementById("editSellingPrice").value);
        const costPrice = parseFloat(document.getElementById("editCostPrice").value);
        const discountVal = document.getElementById("editDiscountPrice").value.trim();
        const discountPrice = discountVal ? parseFloat(discountVal) : null;
        const imageUrl = document.getElementById("editPicUrl").value.trim() || null;

        const saveBtn = document.getElementById("savePricePicBtn");
        saveBtn.disabled = true;
        saveBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin mr-2"></i> Saving Updates...`;

        try {
          const res = await apiFetch(`/api/erp/products/${prodId}/price-pics`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              selling_price: sellingPrice,
              cost_price: costPrice,
              discount_price: discountPrice,
              image_url: imageUrl
            })
          });
          const data = await res.json();
          if (!res.ok) throw new Error(data.detail || "Update failed");

          editPricePicModal.classList.add("hidden");
          alert("Product price and picture updated successfully!");
          loadInventory();
        } catch (err) {
          alert("Error updating price/picture: " + err.message);
        } finally {
          saveBtn.disabled = false;
          saveBtn.innerHTML = `<i class="fa-solid fa-check mr-2"></i> Save Price & Picture Changes`;
        }
      });
    }

    // Traffic & Visitor Controls
    const toggleMaintenance = document.getElementById("toggleMaintenance");
    const manualBlockBtn = document.getElementById("manualBlockBtn");
    const manualBlockIp = document.getElementById("manualBlockIp");
    const refreshVisitorsBtn = document.getElementById("refreshVisitorsBtn");

    if (toggleMaintenance) {
      toggleMaintenance.addEventListener("change", async () => {
        const isMaintenance = toggleMaintenance.checked;
        try {
          await apiFetch("/api/erp/visitors/controls", {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              maintenance_mode: isMaintenance
            })
          });
          alert(isMaintenance ? "Storefront maintenance mode is now ON! Regular customers will see the maintenance notice." : "Storefront maintenance mode is now OFF. Store is live.");
        } catch (err) {
          alert("Error updating maintenance mode: " + err.message);
          toggleMaintenance.checked = !isMaintenance;
        }
      });
    }

    if (manualBlockBtn && manualBlockIp) {
      manualBlockBtn.addEventListener("click", async () => {
        const ip = manualBlockIp.value.trim();
        if (!ip) {
          alert("Please enter a valid IP address to block");
          return;
        }
        const reason = prompt(`Block IP address ${ip}?\nEnter reason:`, "Restricted by store administrator") || "Manual block";
        try {
          await apiFetch("/api/erp/visitors/block-ip", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ip_address: ip, reason: reason })
          });
          manualBlockIp.value = "";
          alert(`IP address ${ip} has been blocked.`);
          loadVisitors();
        } catch (err) {
          alert("Error blocking IP: " + err.message);
        }
      });
    }

    if (refreshVisitorsBtn) {
      refreshVisitorsBtn.addEventListener("click", () => {
        loadVisitors();
      });
    }
  }
});
