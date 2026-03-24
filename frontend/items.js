const itemsMessage = document.getElementById("itemsMessage");
const itemsList = document.getElementById("itemsList");
const availabilityForm = document.getElementById("availabilityForm");
const startDateInput = document.getElementById("startDate");
const expectedReturnDateInput = document.getElementById("expectedReturnDate");
const showAllItemsButton = document.getElementById("showAllItemsButton");
const cartCountMessage = document.getElementById("cartCountMessage");

const token = localStorage.getItem("token");

function setMinDates() {
    const today = new Date().toISOString().split("T")[0];
    startDateInput.min = today;
    expectedReturnDateInput.min = today;
}

function updateCartCountMessage() {
    const cart = JSON.parse(localStorage.getItem("cart") || "[]");

    if (!Array.isArray(cart) || cart.length === 0) {
        cartCountMessage.textContent = "הסל ריק";
        return;
    }

    cartCountMessage.textContent = `יש ${cart.length} פריטים בסל`;
}

setMinDates();
updateCartCountMessage();
loadAllItems();

availabilityForm.addEventListener("submit", function (event) {
    event.preventDefault();

    const startDateValue = startDateInput.value;
    const expectedReturnDateValue = expectedReturnDateInput.value;

    if (startDateValue === "" || expectedReturnDateValue === "") {
        itemsMessage.textContent = "יש למלא את שני התאריכים כדי לסנן לפי זמינות";
        return;
    }

    if (expectedReturnDateValue < startDateValue) {
        itemsMessage.textContent = "תאריך ההחזרה חייב להיות שווה או מאוחר מתאריך ההתחלה";
        return;
    }

    loadAvailableItems(startDateValue, expectedReturnDateValue);
});

showAllItemsButton.addEventListener("click", function () {
    startDateInput.value = "";
    expectedReturnDateInput.value = "";
    setMinDates();
    loadAllItems();
});

startDateInput.addEventListener("change", function () {
        expectedReturnDateInput.min = startDateInput.value;

        if (
            expectedReturnDateInput.value !== "" &&
            expectedReturnDateInput.value < startDateInput.value
        ) {
            expectedReturnDateInput.value = "";
        }
});

async function loadAllItems() {
    itemsMessage.textContent = "טוען את כל הפריטים...";
    itemsList.innerHTML = "";

    try {
        const response = await fetch("http://127.0.0.1:8000/items");
        const data = await response.json();

        if (!response.ok) {
            itemsMessage.textContent = data.detail || "שגיאה בטעינת הפריטים";
            return;
        }

        renderItems(data, "כל הפריטים נטענו בהצלחה");
    }

    catch (error) {
        itemsMessage.textContent = "שגיאה בחיבור לשרת";
        console.error(error);
    }
}

async function loadAvailableItems(startDate, expectedReturnDate) {
    itemsMessage.textContent = "טוען פריטים זמינים...";
    itemsList.innerHTML = "";

    try {
        const url = `http://127.0.0.1:8000/items/available?startDate=${startDate}&expectedReturnDate=${expectedReturnDate}`;
        console.log("Available items URL:", url);
        
        const response = await fetch(url);
        
        const rawText = await response.text();
        console.log("Available items status:", response.status);
        console.log("Available items raw response:", rawText);

        let data;
        try {
            data = JSON.parse(rawText);
        }
        catch {
            data = rawText;
        }

        if (!response.ok) {
            if (typeof data === "object" && data !== null && data.detail) {
                itemsMessage.textContent = Array.isArray(data.detail)
                    ? "שגיאה בפרמפטרים שנשלחו לשרת"
                    : data.detail;
            }
            else {
                itemsMessage.textContent = "שגיאה בטעינת הפריטים הזמינים";
            }
            return;
        }

        renderItems(data, `נמצאו ${data.length} פריטים זמינים`);
    }
    catch (error) {
        itemsMessage.textContent = "שגיאה בחיבור לשרת";
        console.error("loadAvailableItems error:", error);
    }
}

function renderItems(items, successMessage) {
    itemsList.innerHTML = "";
    if (!Array.isArray(items) || items.length === 0) {
        itemsMessage.textContent = "אין פריטים להצגה";
        return;
    }

    itemsMessage.textContent = successMessage;

    items.forEach(function (item) {
        const itemCard = document.createElement("article");
        itemCard.className = "item-card";

        itemCard.innerHTML = `
            <p class="item-category">${item.category || "ללא קטגוריה"}</p>
            <h2 class="item-name">${item.name || "ללא שם"}</h2>
            <p class="item-description">${item.description || "אין תיאור"}</p>
            <p class="item-quantity">כמות כוללת: ${item.quantity ?? "לא ידוע"}</p>
            <p class="item-available-count">כמות זמינה בתאריכים שנבחרו: ${item.availableCount ?? item.quantity ?? "לא ידוע"}</p>
            <p class="item-notes">הערות: ${item.notes || "אין הערות"}</p>
            
            <div class="item-actions">
                <label for="quantity-${item.id}">כמות להשאלה</label>
                <input
                    type="number"
                    id="quantity-${item.id}"
                    class="quantity-input"
                    min="1"
                    max="${item.availableCount ?? item.quantity ?? 1}"
                    value="1"
                >
                <button class="add-to-cart-button">הוסף לסל</button>
                <p class="item-card-message"></p>
            </div>
            `;

        const quantityInput = itemCard.querySelector(".quantity-input");
        const addToCartButton = itemCard.querySelector(".add-to-cart-button");
        const itemCardMessage = itemCard.querySelector(".item-card-message");
        
        addToCartButton.addEventListener("click", function () {
            console.log("clicked add to cart");
            itemCardMessage.textContent = "";
            if (!token) {
                console.log("no token");
                window.location.href = "login.html";
                return;
            }
            
            const requestedQuantity = Number(quantityInput.value);
            const maxAvailable = Number(item.availableCount ?? item.quantity ?? 1);

            if (!Number.isInteger(requestedQuantity) || requestedQuantity < 1) {
                console.log("invalid quantity");
                itemCardMessage.textContent = "יש לבחור כמות חוקית";
                return;
            }

            if (requestedQuantity > maxAvailable) {
                console.log("requsted quantity too high");
                itemCardMessage.textContent = "הכמות המבוקשת גדולה מהכמות הזמינה";
                return;                
            }

            const existingCart = JSON.parse(localStorage.getItem("cart") || "[]");

            const existingItemIndex = existingCart.findIndex(function (cartItem) {
                return (
                    cartItem.itemId === item.id &&
                    cartItem.startDate === startDateInput.value &&
                    cartItem.expectedReturnDate === expectedReturnDateInput.value
                );
            });

            const cartItemData = {
                itemId: item.id,
                itemName: item.name || "",
                category: item.category || "",
                requestedQuantity: requestedQuantity,
                availableCount: maxAvailable,
                startDate: startDateInput.value,
                expectedReturnDate: expectedReturnDateInput.value
            };

            if (existingItemIndex !== -1) {
                existingCart[existingItemIndex].requestedQuantity += requestedQuantity;

                if (existingCart[existingItemIndex].requestedQuantity > maxAvailable) {
                    console.log("total cart quantity too high");
                    itemCardMessage.textContent = "הכמות הכוללת בסל גדולה מהכמות הזמינה";
                    return;
                }
            }
            else {
                existingCart.push(cartItemData);
            }

            localStorage.setItem("cart", JSON.stringify(existingCart));
            updateCartCountMessage();
            console.log("before alert");
            alert(`הפריט "${item.name || "ללא שם"}" נוסף לסל`);            
        });
        itemsList.appendChild(itemCard);
    });
}