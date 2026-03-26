// ================================
// BASE URL
// ================================
const ADMIN_BASE_URL = "https://missing-person-fastapi.onrender.com";
// After Render deployment, change to: const ADMIN_BASE_URL = "https://your-app-name.onrender.com";


// ================================
// SUBMIT ADMIN INMATE REPORT
// ================================
async function submitAdminInmateReport() {

    // ================================
    // Date Validation
    // ================================
    const dobValue = document.getElementById("admin-dob").value;
    const joiningDateValue = document.getElementById("admin-joiningDate").value;
    const currentDate = new Date();

    if (!dobValue) {
        alert("Date of Birth is required.");
        return;
    }

    const dobDate = new Date(dobValue);
    if (dobDate > currentDate) {
        alert("Future Date of Birth is not allowed.");
        return;
    }

    if (!joiningDateValue) {
        alert("Joining Date is required.");
        return;
    }

    const joiningDate = new Date(joiningDateValue);
    if (joiningDate > currentDate) {
        alert("Future Joining Date is not allowed.");
        return;
    }

    if (joiningDate < dobDate) {
        alert("Joining date cannot be before Date of Birth.");
        return;
    }

    // ================================
    // Required Fields Check
    // ================================
    const inmateId  = document.getElementById("admin-inmateId").value.trim();
    const regNo     = document.getElementById("admin-regNo").value.trim();
    const fullName  = document.getElementById("admin-fullName").value.trim();

    if (!inmateId || !regNo || !fullName) {
        alert("Please fill in Inmate ID, Registration No, and Full Name.");
        return;
    }

    // ================================
    // Build FormData
    // ================================
    const formData = new FormData();
    formData.append("inmate_id",       inmateId);
    formData.append("registration_no", regNo);
    formData.append("unique_id",       document.getElementById("admin-uniqueId").value);
    formData.append("status",          document.getElementById("admin-status").value);
    formData.append("full_name",       fullName);
    formData.append("dob",             dobValue);
    formData.append("gender",          document.getElementById("admin-gender").value);
    formData.append("languages",       document.getElementById("admin-languages").value);
    formData.append("address",         document.getElementById("admin-address").value);
    formData.append("joining_date",    joiningDateValue);

    const photoInput = document.getElementById("adminPhotoInput");
    if (photoInput.files.length > 0) {
        formData.append("photo", photoInput.files[0]);
    }

    // ================================
    // Send to FastAPI
    // ================================
    try {
        const response = await fetch(`${ADMIN_BASE_URL}/register-inmate`, {
            method: "POST",
            body: formData
        });

        const result = await response.json();

        if (!response.ok) {
            // FastAPI sends error inside "detail"
            alert(result.detail || "Server error. Please try again.");
            return;
        }

        alert(result.message);
        showDashboard();

    } catch (error) {
        console.error("Error:", error);
        alert("Could not connect to the server. Please try again.");
    }
}


// ================================
// SET DATE MAX TO TODAY
// Prevents browser from allowing future dates in the date pickers
// ================================
window.addEventListener("DOMContentLoaded", function () {
    const today = new Date().toISOString().split("T")[0];

    const dobInput     = document.getElementById("admin-dob");
    const joiningInput = document.getElementById("admin-joiningDate");

    if (dobInput)     dobInput.max     = today;
    if (joiningInput) joiningInput.max = today;
});
