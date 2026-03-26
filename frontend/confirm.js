const confirmDatesMessage = document.getElementById("confirmDatesMessage");
const confirmCartMessage = document.getElementById("confirmCartMessage");
const confirmItemsList = document.getElementById("confirmItemsList");
const confirmForm = document.getElementById("confirmForm");
const borrowerNameInput = document.getElementById("borrowerName");
const borrowerPhoneInput = document.getElementById("borrowerPhone");
const confirmNotesInput = document.getElementById("confirmNotes");
const confirmMessage = document.getElementById("confirmMessage");

const token = localStorage.getItem("token");
const cart = JSON.parse(localStorage.getItem("cart") || "[]");

if (!token) {
    window.location.href = "login.html";
}

renderConfirmPage();

function renderConfirmPage() {
    confirmItemsList.innerHTML = "";

    if (!Array.isArray(cart) || cart.length === 0) {
        confirmDatesMessage.textContent = "לא נבחרו תאריכים";
        confirmCartMessage.textContent = "אין פריטים לאישור";
        confirmForm.style.display = "none";
        return;
    }

    const firstItem = cart[0];
    const startDate = firstItem.startDate || "לא נבחר";
    const expectedReturnDate = firstItem.expectedReturnDate || "לא נבחר";

    
  confirmDatesMessage.textContent = `תאריך התחלה: ${startDate} | תאריך החזרה צפוי: ${expectedReturnDate}`;
  confirmCartMessage.textContent = `יש ${cart.length} פריטים לאישור`;

  cart.forEach(function (cartItem) {
    const confirmItemCard = document.createElement("article");
    confirmItemCard.className = "confirm-item-card";

    confirmItemCard.innerHTML = `
      <p class="confirm-item-category">${cartItem.category || "ללא קטגוריה"}</p>
      <h3 class="confirm-item-name">${cartItem.itemName || "ללא שם"}</h3>
      <p class="confirm-item-quantity">כמות שנבחרה: ${cartItem.requestedQuantity ?? "לא ידוע"}</p>
      <p class="confirm-item-available">כמות זמינה: ${cartItem.availableCount ?? "לא ידוע"}</p>
    `;

    confirmItemsList.appendChild(confirmItemCard);
  });
}

confirmForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    const borrowerNameValue = borrowerNameInput.value.trim();
    const borrowerPhoneValue = borrowerPhoneInput.value.trim();
    const confirmNotesValue = confirmNotesInput.value.trim();

    if (borrowerNameValue === "" || borrowerPhoneValue === "") {
        confirmMessage.textContent = "יש למלא שם וטלפון";
        return;
    }

    if (!Array.isArray(cart) || cart.length === 0) {
        confirmMessage.textContent = "אין פריטים לשליחה";
        return;
    }

    confirmMessage.textContent = "שולח את הקשות ההשאלה...";

    try {
        for (const cartItem of cart) {
            const quantityToSend = Number(cartItem.requestedQuantity ?? 1);

            for (let i = 0; i < quantityToSend; i++) {
                const response = await fetch("http://127.0.0.1:8000/loans", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    itemId: cartItem.itemId,
                    borrowerName: borrowerNameValue,
                    borrowerPhone: borrowerPhoneValue,
                    startDate: cartItem.startDate,
                    expectedReturnDate: cartItem.expectedReturnDate,
                    notes: confirmNotesValue
                })
            });

            const data = await response.json();
            if (!response.ok) {
                confirmMessage.textContent = data.detail || "אחת מבקשות ההשאלה נכשלה במהלך שליחת הכמויות";
                return;
            }
        }
            
    }

    localStorage.removeItem("cart");
    window.location.href = "success.html";
}
    catch (error) {
        confirmMessage.textContent = "שגיאה בחיבור לשרת";
        console.error(error);
    }

});