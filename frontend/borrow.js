const selectedItemMessage = document.getElementById("selectedItemMessage");

const token = localStorage.getItem("token");
const selectedItemId = localStorage.getItem("selectedItemId");
const selectedItemName =localStorage.getItem("selectedItemName");

if (!token) {
    window.location.href = "login.html";
}
else if (!selectedItemId) {
    selectedItemMessage.textContent = "לא נבחר פריט להשאלה";
}
else {
    selectedItemMessage.textContent = `הפריט שנבחר: ${selectedItemName || "ללא שם"}`;
}