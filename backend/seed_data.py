import json
from backend.database import get_db, init_db
from backend.auth import hash_password

def seed_database():
    init_db()
    with get_db() as conn:
        cursor = conn.cursor()

        print("Seeding/Refreshing Rehan Computers database with original copy and expanded accessories...")

        # 1. Store Settings with unique original slogans
        settings = {
            "store_name": "Rehan Laptop & Computer",
            "store_tagline": "Engineered for Performance. Trusted by Generations.",
            "phone": "0300-9607829",
            "whatsapp": "0300-9607829",
            "email": "contact@rehancomputers.pk",
            "address": "Shop #96, 1st Floor, Trust Plaza, Sargodha, Punjab, Pakistan",
            "address_ur": "شاپ نمبر 96، فرسٹ فلور، ٹرسٹ پلازہ، سرگودھا",
            "urdu_slogan": "سرگودھا کا سب سے معتبر ٹیکنالوجی پارٹنر — جہاں ہر مشین اعلیٰ معیار، اصلی پرزوں اور شفافیت کی ضمانت ہے",
            "urdu_banner_text": "مستند امپورٹڈ لیپ ٹاپس، جدید ترین گیمنگ و دفتری لوازمات اور سرجیکل مائیکرو سولڈرنگ ریپئر سینٹر",
            "currency": "PKR",
            "tax_percentage": "0",
            "shipping_flat_rate": "300",
            "free_shipping_min": "25000",
            "receipt_footer": "Thank you for choosing Rehan Laptop & Computer! Shop #96, 1st Floor, Trust Plaza, Sargodha. Helpline: 0300-9607829. 1-Month Checking Warranty covers internal hardware modules."
        }
        for k, v in settings.items():
            cursor.execute("INSERT OR REPLACE INTO store_settings (key, value) VALUES (?, ?)", (k, v))

        # 2. Staff Users (Ensure default users exist)
        users = [
            ("admin", "admin@rehancomputers.pk", hash_password("admin123"), "Muhammad Rehan", "admin", "0300-9607829"),
            ("manager", "manager@rehancomputers.pk", hash_password("manager123"), "Haji Usman", "manager", "0300-1234567"),
            ("cashier", "cashier@rehancomputers.pk", hash_password("cashier123"), "Ali Raza (POS)", "cashier", "0300-7654321"),
            ("tech", "tech@rehancomputers.pk", hash_password("tech123"), "Hamza Khan (Engineer)", "technician", "0300-9876543")
        ]
        for u in users:
            cursor.execute("SELECT id FROM users WHERE username = ?", (u[0],))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, full_name, role, phone)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, u)

        # 3. Categories
        categories = [
            ("Laptops", "laptops", "Directly imported Grade A+ business ultrabooks and executive workstations", "laptop", 1),
            ("Gaming Laptops", "gaming-laptops", "High-FPS gaming rigs equipped with dedicated NVIDIA RTX GPUs and fast refresh displays", "gamepad", 2),
            ("Desktop Computers", "desktop-computers", "Bespoke PC towers, mini workstations, and commercial office systems", "desktop", 3),
            ("LED & Monitors", "led-monitors", "Ultra-sharp IPS, borderless and high-refresh gaming displays", "tv", 4),
            ("Computer Accessories", "accessories", "Mechanical keyboards, high-precision mice, studio webcams, headsets and cooling stands", "mouse", 5),
            ("Storage & Upgrades", "parts-upgrades", "Lightning-fast Gen4 NVMe SSDs, low-latency RAM modules, OEM adapters and batteries", "hdd", 5),
            ("Precision Repair Services", "repair-services", "In-house surgical motherboard chip diagnostics, BIOS recovery, and hinge reconstruction", "wrench", 6),
        ]
        for c in categories:
            cursor.execute("SELECT id FROM categories WHERE slug = ?", (c[1],))
            row = cursor.fetchone()
            if row:
                cursor.execute("UPDATE categories SET name=?, description=?, icon=?, display_order=? WHERE id=?", (c[0], c[2], c[3], c[4], row[0]))
            else:
                cursor.execute("INSERT INTO categories (name, slug, description, icon, display_order) VALUES (?, ?, ?, ?, ?)", c)

        # 4. Brands
        brands = [
            ("HP", "hp", "/static/brands/hp.png", 1),
            ("Dell", "dell", "/static/brands/dell.png", 1),
            ("Lenovo", "lenovo", "/static/brands/lenovo.png", 1),
            ("Asus", "asus", "/static/brands/asus.png", 1),
            ("Acer", "acer", "/static/brands/acer.png", 1),
            ("Apple", "apple", "/static/brands/apple.png", 1),
            ("Samsung", "samsung", "/static/brands/samsung.png", 1),
            ("Logitech", "logitech", "/static/brands/logitech.png", 1),
            ("Redragon", "redragon", "/static/brands/redragon.png", 1),
            ("Kingston", "kingston", "/static/brands/kingston.png", 1),
        ]
        for b in brands:
            cursor.execute("SELECT id FROM brands WHERE slug = ?", (b[1],))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO brands (name, slug, logo_url, is_featured) VALUES (?, ?, ?, ?)", b)

        # Map IDs
        cursor.execute("SELECT id, slug FROM brands")
        b_map = {row[1]: row[0] for row in cursor.fetchall()}
        cursor.execute("SELECT id, slug FROM categories")
        c_map = {row[1]: row[0] for row in cursor.fetchall()}

        # 5. Rich Products & Accessories Catalog
        products = [
            # LAPTOPS
            (
                "HP EliteBook 840 G6 — Core i5 8th Gen Quad-Core",
                "hp-elitebook-840-g6",
                "HP-ELITE-840G6-01",
                b_map.get("hp"),
                c_map.get("laptops"),
                "Grade A+ Used",
                json.dumps({
                    "processor": "Intel Core i5-8365U vPro (Quad Core 4.10 GHz Turbo)",
                    "ram": "16GB DDR4 High-Frequency Memory",
                    "storage": "256GB M.2 PCIe NVMe Solid State Drive",
                    "display": "14.0-inch Full HD (1920x1080) Anti-Glare IPS 300-nits",
                    "graphics": "Intel Ultra HD Graphics 620",
                    "battery": "4+ Hours Active Work Backup (Verified 88%+ Health)",
                    "chassis": "Precision Cut Magnesium-Aluminum Unibody",
                    "security": "Fingerprint Scanner + Windows Hello Facial Recognition IR",
                    "os": "Genuine Windows 11 Pro 64-bit Activated"
                }),
                52000.0,
                58500.0,
                56999.0,
                8,
                2,
                "1 Month Complete Hardware Warranty",
                "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=600&auto=format&fit=crop&q=80",
                json.dumps(["https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=600&auto=format&fit=crop&q=80"]),
                1,
                1
            ),
            (
                "Dell Latitude 7490 Touch Edition — Core i7 8th Gen",
                "dell-latitude-7490-touch",
                "DELL-LAT-7490-02",
                b_map.get("dell"),
                c_map.get("laptops"),
                "Grade A+ Used",
                json.dumps({
                    "processor": "Intel Core i7-8650U (4 Cores, 8 Threads up to 4.20 GHz)",
                    "ram": "16GB DDR4 Dual-Channel RAM",
                    "storage": "512GB High-Speed M.2 NVMe SSD",
                    "display": "14.0-inch FHD (1920x1080) TruBrite Multi-Touch Display",
                    "keyboard": "Ergonomic Backlit Keyboard with Dual Pointing Sticks",
                    "battery": "4.5 Hours Certified Battery Duration",
                    "connectivity": "Thunderbolt 3 Type-C, HDMI 1.4, RJ-45 LAN, Micro-SD",
                    "os": "Windows 11 Pro Genuine"
                }),
                59000.0,
                66000.0,
                63999.0,
                6,
                2,
                "1 Month Component Guarantee",
                "https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=600&auto=format&fit=crop&q=80",
                json.dumps(["https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=600&auto=format&fit=crop&q=80"]),
                1,
                1
            ),
            (
                "Lenovo ThinkPad T480 — Dual Bridge Endurance Beast",
                "lenovo-thinkpad-t480",
                "LEN-TP-T480-03",
                b_map.get("lenovo"),
                c_map.get("laptops"),
                "Grade A+ Used",
                json.dumps({
                    "processor": "Intel Core i5-8250U 8-Threaded Workhorse",
                    "ram": "16GB DDR4 (Expandable to 32GB)",
                    "storage": "256GB NVMe SSD + Additional 2.5 Expansion Bay",
                    "display": "14.0-inch Anti-Glare IPS 1080p Crystal Clear",
                    "battery_tech": "Dual Battery PowerBridge Architecture (Up to 6+ Hours)",
                    "durability": "MIL-STD-810G Military Grade Tested for Drops and Dust",
                    "keyboard": "World-Class Spill-Resistant ThinkPad Key Action",
                    "os": "Windows 11 Pro Enterprise Ready"
                }),
                54000.0,
                61000.0,
                58500.0,
                10,
                3,
                "1 Month Checking Warranty",
                "https://images.unsplash.com/photo-1611078489935-0cb964de46d6?w=600&auto=format&fit=crop&q=80",
                json.dumps(["https://images.unsplash.com/photo-1611078489935-0cb964de46d6?w=600&auto=format&fit=crop&q=80"]),
                1,
                1
            ),
            (
                "Asus TUF Gaming F15 — Core i7 11th Gen + RTX 3050",
                "asus-tuf-gaming-f15",
                "ASUS-TUF-F15-04",
                b_map.get("asus"),
                c_map.get("gaming-laptops"),
                "Brand New",
                json.dumps({
                    "processor": "Intel Core i7-11800H Octa-Core (16 Threads, 4.60 GHz Max)",
                    "graphics": "NVIDIA GeForce RTX 3050 4GB GDDR6 Dedicated Ray-Tracing",
                    "ram": "16GB DDR4 3200MHz Gaming Memory",
                    "storage": "512GB PCIe 3.0 NVMe SSD",
                    "display": "15.6-inch 144Hz Smooth Adaptive-Sync Esports Screen",
                    "cooling": "Self-Cleaning Dual Fan Turbos with Dedicated Heatpipes",
                    "audio": "DTS:X Ultra 7.1 Virtual Surround Sound",
                    "os": "Windows 11 Home Licensed"
                }),
                195000.0,
                218000.0,
                209999.0,
                3,
                1,
                "1 Year Official Manufacturer Warranty",
                "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=600&auto=format&fit=crop&q=80",
                json.dumps(["https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=600&auto=format&fit=crop&q=80"]),
                1,
                1
            ),
            (
                "Apple MacBook Air 13-inch (Apple Silicon M1, Space Gray)",
                "apple-macbook-air-m1",
                "APL-MBA-M1-08",
                b_map.get("apple"),
                c_map.get("laptops"),
                "Grade A+ Used",
                json.dumps({
                    "chip": "Apple M1 System on Chip (8-Core CPU + 7-Core GPU)",
                    "ram": "8GB Unified Memory High Bandwidth",
                    "storage": "256GB Ultra-Responsive Solid State Drive",
                    "display": "13.3-inch Retina Display with True Tone Color Science",
                    "battery": "Staggering 15+ Hours Battery Runtime (Cycle Count < 150)",
                    "weight": "Featherlight 1.29 kg Precision Aluminum",
                    "os": "macOS Sonoma Pre-Configured"
                }),
                145000.0,
                165000.0,
                159000.0,
                2,
                1,
                "1 Month Physical & Battery Warranty",
                "https://images.unsplash.com/photo-1611186871348-b1ce696e52c9?w=600&auto=format&fit=crop&q=80",
                json.dumps(["https://images.unsplash.com/photo-1611186871348-b1ce696e52c9?w=600&auto=format&fit=crop&q=80"]),
                1,
                1
            ),
            (
                "Dell Precision 7530 Industrial CAD/3D Workstation",
                "dell-precision-7530",
                "DELL-PREC-7530-06",
                b_map.get("dell"),
                c_map.get("laptops"),
                "Refurbished",
                json.dumps({
                    "processor": "Intel Core i7-8850H 6 Cores 12 Threads (4.30 GHz)",
                    "ram": "32GB DDR4 (Up to 128GB across 4 slots)",
                    "storage": "512GB M.2 NVMe (Triple NVMe Slots Built-in)",
                    "graphics": "NVIDIA Quadro P2000 4GB ISV-Certified for SolidWorks/3Ds Max",
                    "display": "15.6-inch UltraSharp FHD IPS Wide-Gamut Anti-Glare",
                    "chassis": "Heavy-Duty Magnesium Shell with Thermal Dual Exhaust",
                    "os": "Windows 11 Pro for Workstations"
                }),
                110000.0,
                128000.0,
                122500.0,
                4,
                1,
                "1 Month Direct Replacement Guarantee",
                "https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2?w=600&auto=format&fit=crop&q=80",
                json.dumps(["https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2?w=600&auto=format&fit=crop&q=80"]),
                1,
                1
            ),

            # ACCESSORIES EXPANSION
            (
                "Logitech MX Master 3S Wireless Ergonomic Mouse",
                "logitech-mx-master-3s",
                "LOGI-MXM3S-ACC01",
                b_map.get("logitech", b_map.get("hp")),
                c_map.get("accessories"),
                "Brand New",
                json.dumps({
                    "sensor": "8,000 DPI Darkfield Laser Tracking (Works on Glass)",
                    "clicks": "Quiet Click Technology (90% Noise Reduction)",
                    "scroll": "MagSpeed Electromagnetic Scrolling (1,000 lines/sec)",
                    "connectivity": "Bluetooth Low Energy + Logi Bolt USB Receiver",
                    "battery": "70 Days on Full Charge, 3 Hours from 1 Min Quick Charge",
                    "ergonomics": "Hand-Sculpted Silhouette with Thumb Gesture Controls"
                }),
                21000.0,
                26000.0,
                24500.0,
                15,
                3,
                "1 Year Official Replacement Warranty",
                "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=600&auto=format&fit=crop&q=80",
                json.dumps(["https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=600&auto=format&fit=crop&q=80"]),
                1,
                1
            ),
            (
                "Redragon K552 KUMARA RGB Mechanical Gaming Keyboard",
                "redragon-k552-kumara-rgb",
                "RDR-K552-ACC02",
                b_map.get("redragon", b_map.get("asus")),
                c_map.get("accessories"),
                "Brand New",
                json.dumps({
                    "switches": "Custom Mechanical Outemu Blue Tactile Clicky Switches",
                    "lighting": "18 RGB Backlighting Modes with 5 Brightness Levels",
                    "build": "Solid Aircraft-Grade Aluminum Base Plate & ABS Housing",
                    "anti_ghosting": "Full N-Key Rollover Anti-Ghosting Keys",
                    "cable": "Gold-Plated High-Speed Corrosion Free USB Connector",
                    "durability": "50 Million Keystroke Longevity Tested"
                }),
                7800.0,
                11000.0,
                9800.0,
                18,
                4,
                "6 Months Replacement Warranty",
                "https://images.unsplash.com/photo-1595225476474-87563907a212?w=600&auto=format&fit=crop&q=80",
                json.dumps(["https://images.unsplash.com/photo-1595225476474-87563907a212?w=600&auto=format&fit=crop&q=80"]),
                1,
                1
            ),
            (
                "Logitech C920 HD Pro Streaming Webcam (1080p 60fps)",
                "logitech-c920-hd-pro-webcam",
                "LOGI-C920-ACC03",
                b_map.get("logitech", b_map.get("dell")),
                c_map.get("accessories"),
                "Brand New",
                json.dumps({
                    "video_resolution": "Full HD 1080p at 30/60fps with Premium Glass Lens",
                    "microphones": "Dual Stereo Omnidirectional Noise-Cancelling Mics",
                    "lighting": "Automatic HD Light Correction (RightLight 2 Technology)",
                    "field_of_view": "78-Degree Diagonal Field of View",
                    "mounting": "Universal Clip Fits Any Laptop Bezel or Tripod Mount",
                    "ideal_for": "Freelancers, Zoom Conferences, Teaching, Content Creation"
                }),
                15000.0,
                19500.0,
                18500.0,
                12,
                3,
                "1 Year Official Warranty",
                "https://images.unsplash.com/photo-1588508065123-287b28e013da?w=600&auto=format&fit=crop&q=80",
                json.dumps(["https://images.unsplash.com/photo-1588508065123-287b28e013da?w=600&auto=format&fit=crop&q=80"]),
                1,
                1
            ),
            (
                "Samsung T7 Shield 1TB Rugged External NVMe SSD",
                "samsung-t7-shield-1tb-ssd",
                "SAMS-T7S-ACC04",
                b_map.get("samsung"),
                c_map.get("parts-upgrades"),
                "Brand New",
                json.dumps({
                    "speed": "Up to 1,050 MB/s Sequential Read & 1,000 MB/s Write",
                    "durability": "IP65 Rated Water, Dust & Rain Resistance",
                    "protection": "Drop-Resistant up to 3 Meters with Rubber Armor",
                    "security": "AES 256-Bit Hardware Encryption with Password Protection",
                    "compatibility": "Plug & Play with Windows, Mac, Android, and Gaming Consoles",
                    "cables": "Includes USB-C to USB-C and USB-C to USB-A Cables"
                }),
                24500.0,
                31000.0,
                29500.0,
                10,
                2,
                "3 Years Brand Warranty",
                "https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?w=600&auto=format&fit=crop&q=80",
                json.dumps(["https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?w=600&auto=format&fit=crop&q=80"]),
                1,
                1
            ),
            (
                "Baseus 7-in-1 Aluminum USB-C 4K 60Hz Multiport Dock",
                "baseus-7in1-usbc-dock",
                "BAS-DOCK-7IN1-ACC05",
                b_map.get("hp"),
                c_map.get("accessories"),
                "Brand New",
                json.dumps({
                    "hdmi_port": "4K@60Hz Ultra HD High-Refresh Video Output",
                    "power_delivery": "100W USB-C PD Supercharge Pass-Through",
                    "usb_expansion": "3x USB 3.0 5Gbps High-Speed Data Ports",
                    "card_reader": "SD and TF/MicroSD High-Speed Simultaneous Read",
                    "heat_dissipation": "Sandblasted Aviation-Grade Anodized Aluminum Housing",
                    "compatibility": "Engineered for MacBooks, ThinkPads, EliteBooks, Latitudes"
                }),
                6400.0,
                9200.0,
                8200.0,
                20,
                4,
                "6 Months Direct Replacement Guarantee",
                "https://images.unsplash.com/photo-1544652478-6653e09f18a2?w=600&auto=format&fit=crop&q=80",
                json.dumps(["https://images.unsplash.com/photo-1544652478-6653e09f18a2?w=600&auto=format&fit=crop&q=80"]),
                0,
                1
            ),
            (
                "DeepCool Multi Core X6 Quad-Fan Ergonomic Cooling Stand",
                "deepcool-multicore-x6-cooler",
                "DC-MCX6-ACC06",
                b_map.get("asus"),
                c_map.get("accessories"),
                "Brand New",
                json.dumps({
                    "cooling_tech": "4 High-Velocity Silent Turbo Fans (2x 140mm + 2x 100mm)",
                    "fan_modes": "4 Distinct Status Modes: 4 Fans On, 2 Upper, 2 Lower, Off",
                    "ergonomics": "Dual Viewing Angles for Natural Neck Alignment",
                    "compatibility": "Accommodates Laptops from 13.3-inch up to 17.3-inch",
                    "ports": "Built-in Dual USB 2.0 Passthrough Ports",
                    "airflow": "High Permeability Metal Mesh Prevents Thermal Throttling"
                }),
                4800.0,
                7200.0,
                6400.0,
                16,
                3,
                "6 Months Warranty",
                "https://images.unsplash.com/photo-1587202372775-e229f172b9d7?w=600&auto=format&fit=crop&q=80",
                json.dumps(["https://images.unsplash.com/photo-1587202372775-e229f172b9d7?w=600&auto=format&fit=crop&q=80"]),
                0,
                1
            ),
            (
                "HyperX Cloud Stinger 2 Lightweight 7.1 Gaming Headset",
                "hyperx-cloud-stinger-2-headset",
                "HPX-CS2-ACC07",
                b_map.get("hp"),
                c_map.get("accessories"),
                "Brand New",
                json.dumps({
                    "drivers": "50mm Directional Drivers for Pinpoint In-Game Spatial Audio",
                    "ear_cushions": "Signature HyperX Soft Memory Foam and Premium Leatherette",
                    "microphone": "Swivel-to-Mute Passive Noise-Cancelling Flexible Mic",
                    "controls": "On-Earcup Audio Volume Slider for Instant Adjustments",
                    "weight": "Featherlight 275g Frame for Long Gaming & Call Sessions",
                    "compatibility": "PC, Laptop, PS5, Xbox, Nintendo Switch, Mobile Devices"
                }),
                11800.0,
                16500.0,
                14800.0,
                14,
                3,
                "1 Year Hardware Warranty",
                "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&auto=format&fit=crop&q=80",
                json.dumps(["https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&auto=format&fit=crop&q=80"]),
                0,
                1
            ),
            (
                "Tigernu Anti-Theft Water-Resistant 15.6 Laptop Backpack",
                "tigernu-antitheft-laptop-backpack",
                "TIG-BAG-156-ACC08",
                b_map.get("lenovo"),
                c_map.get("accessories"),
                "Brand New",
                json.dumps({
                    "material": "High-Density Scratchproof & Splash-Resistant Oxford Fabric",
                    "zipper": "Patented Double-Layer Puncture-Proof Anti-Theft Zipper",
                    "laptop_pocket": "360-Degree Air-Cushioned Shockproof Pocket (Fits up to 15.6)",
                    "usb_port": "Integrated External USB Charging Pass-through",
                    "hidden_pocket": "RFID-Blocking Lumbar Concealed Security Pocket for Passport/Cash",
                    "comfort": "Orthopedic S-Shape Honeycomb Breathable Shoulder Straps"
                }),
                5800.0,
                8500.0,
                7500.0,
                22,
                5,
                "1 Year Stitch & Zipper Warranty",
                "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&auto=format&fit=crop&q=80",
                json.dumps(["https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&auto=format&fit=crop&q=80"]),
                0,
                1
            ),
            (
                "Kingston KC3000 1TB PCIe 4.0 NVMe M.2 SSD (7,000 MB/s)",
                "kingston-kc3000-1tb-nvme",
                "KNG-KC3000-1TB-ACC09",
                b_map.get("kingston", b_map.get("hp")),
                c_map.get("parts-upgrades"),
                "Brand New",
                json.dumps({
                    "read_speed": "Blistering 7,000 MB/s Sequential Read Performance",
                    "write_speed": "Up to 6,000 MB/s Sequential Write Speed",
                    "controller": "Phison E18 Gen4x4 Controller with Micron 176-Layer 3D TLC",
                    "heat_spreader": "Low-Profile Graphene Aluminum Heat Dissipation Sheet",
                    "endurance": "800 TBW (Terabytes Written) Exceptional Longevity",
                    "compatibility": "Compatible with Gen4 Laptops, Desktops, and PS5 Console"
                }),
                21000.0,
                28000.0,
                26000.0,
                15,
                3,
                "5 Years Brand Warranty",
                "https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?w=600&auto=format&fit=crop&q=80",
                json.dumps(["https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?w=600&auto=format&fit=crop&q=80"]),
                1,
                1
            ),
            (
                "Crucial 16GB DDR4 3200MHz SODIMM Laptop Memory Module",
                "crucial-16gb-ddr4-3200-ram",
                "CRU-RAM-16GB-ACC10",
                b_map.get("dell"),
                c_map.get("parts-upgrades"),
                "Brand New",
                json.dumps({
                    "capacity": "16GB Single High-Density SODIMM",
                    "speed": "DDR4-3200 MHz (PC4-25600) Non-ECC Unbuffered",
                    "voltage": "1.2V Low Voltage for Reduced Battery Consumption",
                    "latency": "CL22 Low Latency Timings",
                    "compatibility": "Plug & Play Instant Upgrade for HP, Dell, Lenovo, and Asus Laptops"
                }),
                6800.0,
                9900.0,
                8900.0,
                35,
                5,
                "Lifetime Limited Brand Warranty",
                "https://images.unsplash.com/photo-1562976540-1502c2145186?w=600&auto=format&fit=crop&q=80",
                json.dumps(["https://images.unsplash.com/photo-1562976540-1502c2145186?w=600&auto=format&fit=crop&q=80"]),
                0,
                1
            ),
            (
                "Original Lenovo 65W USB-C Rapid Fast Power Adapter",
                "lenovo-original-65w-usbc-charger",
                "LEN-CHG-65W-ACC11",
                b_map.get("lenovo"),
                c_map.get("parts-upgrades"),
                "Brand New",
                json.dumps({
                    "power_output": "65W Smart USB Power Delivery (PD 3.0)",
                    "voltage_profiles": "20V/3.25A, 15V/3A, 9V/2A, 5V/2A Fast Adaptation",
                    "protections": "Built-in Surge, Over-Voltage, and Short-Circuit Protection",
                    "cable": "High-Flexibility Heavy-Gauge USB-C Cable (1.8 Meters)",
                    "compatibility": "ThinkPad X1, T14, Yoga, Dell XPS, HP Spectre, and MacBooks"
                }),
                3200.0,
                4900.0,
                4200.0,
                25,
                5,
                "6 Months Replacement Warranty",
                "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=600&auto=format&fit=crop&q=80",
                json.dumps(["https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=600&auto=format&fit=crop&q=80"]),
                0,
                1
            ),
            (
                "Screen Mom Non-Toxic Anti-Static Display Cleaning Kit",
                "screen-mom-anti-static-cleaner",
                "SCM-KIT-CLEAN-ACC12",
                b_map.get("samsung"),
                c_map.get("accessories"),
                "Brand New",
                json.dumps({
                    "formula": "100% Alcohol, Ammonia, and Phosphate Free (Safe for All Screen Coatings)",
                    "bottle_size": "Large 250ml Fine-Mist Spray (Over 1,572 Sprays per Bottle)",
                    "cloth": "Plush 15.75x15.75 inch Ultra-Fine Lint-Free Microfiber Detailing Towel",
                    "safe_on": "Retina Displays, Matte Anti-Glare IPS, OLED, Touchscreens, and Eyewear",
                    "finish": "Leaves a Streak-Free, Static-Repelling Dust Shield"
                }),
                1700.0,
                2900.0,
                2400.0,
                40,
                8,
                "Money-Back Satisfaction Guarantee",
                "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=600&auto=format&fit=crop&q=80",
                json.dumps(["https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=600&auto=format&fit=crop&q=80"]),
                0,
                1
            )
        ]

        # Insert or update products
        for p in products:
            cursor.execute("SELECT id FROM products WHERE slug = ?", (p[1],))
            p_exist = cursor.fetchone()
            if p_exist:
                cursor.execute("""
                    UPDATE products SET 
                        title=?, sku=?, brand_id=?, category_id=?, condition=?, specs=?,
                        cost_price=?, selling_price=?, discount_price=?, stock_quantity=?,
                        min_stock_alert=?, warranty_period=?, image_url=?, is_featured=?, is_active=1
                    WHERE id=?
                """, (p[0], p[2], p[3], p[4], p[5], p[6], p[7], p[8], p[9], p[10], p[11], p[12], p[13], p[14], p_exist[0]))
            else:
                cursor.execute("""
                    INSERT INTO products (
                        title, slug, sku, brand_id, category_id, condition, specs,
                        cost_price, selling_price, discount_price, stock_quantity, min_stock_alert,
                        warranty_period, image_url, gallery, is_featured, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """, (p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7], p[8], p[9], p[10], p[11], p[12], p[13], p[14], p[15]))

        print(f"Product & accessories catalog populated successfully! Total items: {len(products)}")

if __name__ == "__main__":
    seed_database()
