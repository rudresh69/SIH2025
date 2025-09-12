// Get HTML elements
const alertBox = document.getElementById("alertBox");
const alertText = document.getElementById("alertText");
const details = document.getElementById("details");
const body = document.getElementById("body");
const alarmSound = document.getElementById("alarmSound");
const startBtn = document.getElementById("startBtn");

// Enable audio playback on user interaction
startBtn.addEventListener("click", () => {
    alarmSound.play().then(() => {
        alarmSound.pause();       // preload sound
        alarmSound.currentTime = 0;
    }).catch(err => console.log("Audio blocked:", err));
    startBtn.style.display = "none"; // hide start button
});

// Function to trigger alerts
function triggerAlert(type, location = "Highway Road") {
    switch(type) {
        case "safe":
            alertBox.style.backgroundColor = "green";
            alertText.textContent = `Status: Safe ✅`;
            details.textContent = `All clear at ${location}.`;
            body.style.backgroundColor = "white";
            alarmSound.pause();
            alarmSound.currentTime = 0;
            break;

        case "warning":
            alertBox.style.backgroundColor = "yellow";
            alertText.textContent = `Status: Warning ⚠️`;
            details.textContent = `Be cautious at ${location}.`;
            body.style.backgroundColor = "white";
            alarmSound.pause();
            alarmSound.currentTime = 0;
            break;

        case "emergency":
            alertBox.style.backgroundColor = "red";
            alertText.textContent = `Status: Emergency 🚨`;
            details.textContent = `Immediate danger at ${location}!`;
            body.style.backgroundColor = "red";
            alarmSound.play(); // play siren
            break;

        default:
            console.warn("Unknown alert type:", type);
    }
}

// Manual test buttons (optional)
document.body.insertAdjacentHTML('beforeend', `
<div style="margin-top:20px;">
    <button onclick="triggerAlert('safe')">Safe</button>
    <button onclick="triggerAlert('warning')">Warning</button>
    <button onclick="triggerAlert('emergency')">Emergency</button>
</div>
`);

// Example automatic alerts for testing
setTimeout(() => triggerAlert("warning"), 3000);    // 3 sec later
setTimeout(() => triggerAlert("emergency"), 6000);  // 6 sec later
setTimeout(() => triggerAlert("safe"), 10000);      // 10 sec later
