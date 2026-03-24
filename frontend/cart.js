// console.log("cart.js loaded");

const cartDatesMessage = document.getElementById("cartDatesMessage");
const cartMessage = document.getElementById("cartMessage");
const cartItemsList = document.getElementById("cartItemsList");

const cart = JSON.parse(localStorage.getItem("cart") || []);

renderCart();

function renderCart() {
    cartItemsList.innerHTML = "";

    if (!Array.isArray(cart) || cart.length === 0) {
        cartDatesMessage.textContent = "לא נבחרו עדיין תאריכים";
        cartMessage.textContent = "הסל ריק";
        return;
    }

    const firstItem = cart[0];
    const startDate = firstItem.startDate || "לא נבחר";
    const expectedReturnDate = firstItem.expectedReturnDate || "לא נבחר";

    cartDatesMessage.textContent = `תאריך התחלה: ${startDate} | תאריך החזרה צפוי: ${expectedReturnDate}`;
    cartMessage.textContent = `נמצאו ${cart.length} פריטים בסל`;

    cart.forEach(function (cartItem, index) {
        const cartItemCard = document.createElement("article");
        cartItemCard.className = "cart-item-card";

        cartItemCard.innerHTML = `
            <p class="cart-item-category">${cartItem.category || "ללא קטגוריה"}</p>
            <h3 class="cart-item-name">${cartItem.itemName || "ללא שם"}</h3>
            <p class="cart-item-available">כמות זמינה: ${cartItem.availableCount ?? "לא ידוע"}</p>

            <label for="cart-quantity-${index}">כמות נבחרת</label>
            <input
            type="number"
            id="cart-quantity-${index}"
            class="cart-quantity-input"
            min="1"
            max="${cartItem.availableCount ?? 1}"
            value="${cartItem.requestedQuantity ?? 1}"
            >

            <button class="remove-cart-item-button">הסר מהסל</button>
        `;
        
        const quantityInput = cartItemCard.querySelector(".cart-quantity-input");
        const removeButton = cartItemCard.querySelector(".remove-cart-item-button");
        
        quantityInput.addEventListener("change", function () {
            updateCartItemQuantity(index, quantityInput.value);
        });

        removeButton.addEventListener("click", function () {
            removeCartItem(index);
        });

        cartItemsList.appendChild(cartItemCard);
    });
}

function removeCartItem(indexToRemove) {
    const currentCart = JSON.parse(localStorage.getItem("cart") || "[]");
    currentCart.splice(indexToRemove, 1);
    localStorage.setItem("cart", JSON.stringify(currentCart));
    window.location.reload();
}

function updateCartItemQuantity(indexToUpdate, newQuantityValue) {
    const currentCart = JSON.parse(localStorage.getItem("cart") || "[]");
    const parsedQuantity = Number(newQuantityValue);

    if (!Number.isInteger(parsedQuantity) || parsedQuantity < 1) {
        alert("יש לבחור כמות חוקית");
        return;
    }

    const itemToUpdate = currentCart[indexToUpdate];

    if (!itemToUpdate) {
        return;
    }

    if (parsedQuantity > Number(itemToUpdate.availableCount ?? 1)) {
        alert("הכמות שנבחרה גדולה מהכמות הזמינה");
        return;
    }

    currentCart[indexToUpdate].requestedQuantity = parsedQuantity;

    localStorage.setItem("cart", JSON.stringify(currentCart));
    window.location.reload();
}