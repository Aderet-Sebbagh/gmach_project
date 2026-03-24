const loginForm = document.getElementById("loginForm")
const phoneInput = document.getElementById("phone")
const passwordInput = document.getElementById("password")
const loginMessage = document.getElementById("loginMessage")

loginForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    const phoneValue = phoneInput.value.trim();
    const passwordValue = passwordInput.value.trim();

    if (phoneValue === "" || passwordValue === "") {
        loginMessage.textContent = "יש למלא טלפון וסיסמא";
        return;
    }

    loginMessage.textContent = "מתחבר...";

    try {
        const response = await fetch("http://127.0.0.1:8000/auth/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                phone: phoneValue,
                password: passwordValue
            })
        });

        const data = await response.json();

        if (!response.ok) {
            loginMessage.textContent = data.detail || "ההתחברות נכשלה";
            return;
        }

        localStorage.setItem("token", data.token);
        localStorage.setItem("role", data.role);

        loginMessage.textContent = "ההתחברות הצליחה";
        
        window.location.href = "items.html";
    }

    catch (error) {
        loginMessage.textContent = "שגיאה בחיבור לשרת";
        console.error(error);
    }
});