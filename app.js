// Odatdagi boshlang'ich ma'lumotlar
const initialProducts = [
    { id: 1, name: 'MacBook Pro M2', category: 'Elektronika', quantity: 15, unit: 'dona', min: 5 },
    { id: 2, name: 'A4 Qog\'oz (Svetocopy)', category: 'Kantselyariya', quantity: 3, unit: 'quti', min: 10 },
    { id: 3, name: 'Simsiz Sishqoncha', category: 'Elektronika', quantity: 0, unit: 'dona', min: 8 },
    { id: 4, name: 'Zavod Suyuqligi (Moy)', category: 'Xom-ashyo', quantity: 45.5, unit: 'litr', min: 50 },
];

// Mahsulotlar massivini LocalStorage'dan olish
let products;
try {
    products = JSON.parse(localStorage.getItem('inventory_products'));
    if (!products) {
        products = initialProducts.map(p => ({...p}));
        localStorage.setItem('inventory_products', JSON.stringify(products));
    }
} catch (e) {
    console.warn("LocalStorage ishlamayapti, ma'lumotlar vaqtincha xotirada saqlanadi.", e);
    products = initialProducts.map(p => ({...p}));
}

// DOM elementlari
const productsTable = document.getElementById('tableBody');
const searchInput = document.getElementById('searchInput');
const addProductBtn = document.getElementById('addProductBtn');
const productModal = document.getElementById('productModal');
const closeModalBtn = document.getElementById('closeModalBtn');
const cancelBtn = document.getElementById('cancelBtn');
const productForm = document.getElementById('productForm');

// Modal maydonlari
const modalTitle = document.getElementById('modalTitle');
const productId = document.getElementById('productId');
const productName = document.getElementById('productName');
const productCategory = document.getElementById('productCategory');
const productQuantity = document.getElementById('productQuantity');
const productUnit = document.getElementById('productUnit');
const productMin = document.getElementById('productMin');

// Statistika elementlari
const totalProductsEl = document.getElementById('totalProducts');
const lowStockProductsEl = document.getElementById('lowStockProducts');
const outOfStockProductsEl = document.getElementById('outOfStockProducts');

// Boshlang'ich yuklash
function init() {
    renderTable();
    updateDashboard();
}

// Jadvalni chizish
function renderTable(filter = '') {
    productsTable.innerHTML = '';
    
    const filteredProducts = products.filter(p => 
        p.name.toLowerCase().includes(filter.toLowerCase()) || 
        p.category.toLowerCase().includes(filter.toLowerCase())
    );

    if(filteredProducts.length === 0) {
        productsTable.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-secondary); padding: 30px;">Mahsulot topilmadi</td></tr>`;
        return;
    }

    filteredProducts.forEach(product => {
        const tr = document.createElement('tr');
        
        // Statusni aniqlash
        let statusHtml = '';
        if (product.quantity <= 0) {
            statusHtml = '<span class="status-badge status-danger">Tugagan</span>';
        } else if (product.quantity <= product.min) {
            statusHtml = '<span class="status-badge status-warning">Kam qolgan</span>';
        } else {
            statusHtml = '<span class="status-badge status-normal">Yaxshi</span>';
        }

        tr.innerHTML = `
            <td><span class="product-name">${product.name}</span></td>
            <td><span class="category-tag">${product.category}</span></td>
            <td><strong>${product.quantity}</strong> <span style="color: var(--text-secondary); font-size:0.85rem;">${product.unit}</span></td>
            <td>${product.min} <span style="color: var(--text-secondary); font-size:0.85rem;">${product.unit}</span></td>
            <td>${statusHtml}</td>
            <td class="actions">
                <button class="btn-icon edit" onclick="editProduct(${product.id})" title="Tahrirlash"><i class="fa-solid fa-pen"></i></button>
                <button class="btn-icon delete" onclick="deleteProduct(${product.id})" title="O'chirish"><i class="fa-solid fa-trash"></i></button>
            </td>
        `;
        productsTable.appendChild(tr);
    });
}

// Statistikani yangilash
function updateDashboard() {
    const total = products.length;
    const lowStock = products.filter(p => p.quantity > 0 && p.quantity <= p.min).length;
    const outOfStock = products.filter(p => p.quantity <= 0).length;

    animateValue(totalProductsEl, parseInt(totalProductsEl.innerText) || 0, total);
    animateValue(lowStockProductsEl, parseInt(lowStockProductsEl.innerText) || 0, lowStock);
    animateValue(outOfStockProductsEl, parseInt(outOfStockProductsEl.innerText) || 0, outOfStock);
}

// Raqamlarni animatsiya bilan o'zgartirish
function animateValue(obj, start, end, duration = 800) {
    if (start === end) {
        obj.innerHTML = end;
        return;
    }
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        // easeOutQuart
        const easeProgress = 1 - Math.pow(1 - progress, 4);
        obj.innerHTML = Math.floor(easeProgress * (end - start) + start);
        if (progress < 1) {
            window.requestAnimationFrame(step);
        } else {
            obj.innerHTML = end;
        }
    };
    window.requestAnimationFrame(step);
}

// Modal ochish
function openModal(editMode = false) {
    productModal.classList.add('show');
    if (!editMode) {
        modalTitle.innerText = "Yangi Mahsulot Qo'shish";
        productForm.reset();
        productId.value = '';
    }
    setTimeout(() => productName.focus(), 100);
}

// Modal yopish
function closeModal() {
    productModal.classList.remove('show');
}

// Saqlash / Tahrirlash
productForm.addEventListener('submit', function(e) {
    e.preventDefault();
    
    const qty = parseFloat(productQuantity.value);
    const minQty = parseFloat(productMin.value);

    const newProduct = {
        id: productId.value ? parseInt(productId.value) : Date.now(),
        name: productName.value.trim(),
        category: productCategory.value.trim(),
        quantity: isNaN(qty) ? 0 : qty,
        unit: productUnit.value,
        min: isNaN(minQty) ? 0 : minQty
    };

    if (productId.value) {
        // Tahrirlash
        const index = products.findIndex(p => p.id === newProduct.id);
        if (index !== -1) {
            products[index] = newProduct;
        }
    } else {
        // Yangi qo'shish
        products.unshift(newProduct); // Boshiga qo'shish
    }

    saveData();
    renderTable(searchInput.value);
    updateDashboard();
    closeModal();
});

// O'chirish
window.deleteProduct = function(id) {
    const product = products.find(p => p.id === id);
    if(confirm(\`Rostdan ham "\${product.name}" mahsulotini o'chirmoqchimisiz?\`)) {
        products = products.filter(p => p.id !== id);
        saveData();
        renderTable(searchInput.value);
        updateDashboard();
    }
}

// Tahrirlash uchun yuklash
window.editProduct = function(id) {
    const product = products.find(p => p.id === id);
    if(product) {
        modalTitle.innerText = "Mahsulotni Tahrirlash";
        productId.value = product.id;
        productName.value = product.name;
        productCategory.value = product.category;
        productQuantity.value = product.quantity;
        productUnit.value = product.unit;
        productMin.value = product.min;
        openModal(true);
    }
}

// LocalStorage ga saqlash
function saveData() {
    try {
        localStorage.setItem('inventory_products', JSON.stringify(products));
    } catch (e) {
        console.warn("Saqlashda xatolik (LocalStorage):", e);
    }
}

// Qidiruv
searchInput.addEventListener('input', (e) => {
    renderTable(e.target.value);
});

// Event Listeners
addProductBtn.addEventListener('click', () => openModal(false));
closeModalBtn.addEventListener('click', closeModal);
cancelBtn.addEventListener('click', closeModal);

// Modal tashqarisiga bossa yopish
productModal.addEventListener('click', (e) => {
    if (e.target === productModal) {
        closeModal();
    }
});

// Esc tugmasi bosilganda modalni yopish
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && productModal.classList.contains('show')) {
        closeModal();
    }
});

// Ishga tushirish
init();
