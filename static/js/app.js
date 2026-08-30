// Mobile Sidebar & Overlay Toggle
function toggleMobileSidebar(e) {
    if (e) e.stopPropagation();
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("sidebarOverlay");
    if (sidebar) sidebar.classList.toggle("show");
    if (overlay) overlay.classList.toggle("show");
}

document.addEventListener("DOMContentLoaded", function() {
    document.getElementById("menuBtn")?.addEventListener("click", toggleMobileSidebar);
    document.getElementById("sidebarOverlay")?.addEventListener("click", toggleMobileSidebar);
});

// Close sidebar on document click outside for mobile
document.addEventListener("click", function(e) {
    const sidebar = document.getElementById("sidebar");
    const menuBtn = document.getElementById("menuBtn");
    const overlay = document.getElementById("sidebarOverlay");
    if (window.innerWidth < 992 && sidebar && sidebar.classList.contains("show")) {
        if (!sidebar.contains(e.target) && (!menuBtn || !menuBtn.contains(e.target))) {
            sidebar.classList.remove("show");
            if (overlay) overlay.classList.remove("show");
        }
    }
});

// Relocate all modal elements to document.body so they are never trapped in low stacking contexts
function relocateModalsToBody() {
    document.querySelectorAll(".modal").forEach(function(modal) {
        if (modal.parentNode !== document.body) {
            document.body.appendChild(modal);
        }
    });
}

document.addEventListener("DOMContentLoaded", relocateModalsToBody);
document.addEventListener("show.bs.modal", relocateModalsToBody);
document.addEventListener("click", function(e) {
    if (e.target && e.target.closest('[data-bs-toggle="modal"]')) {
        relocateModalsToBody();
    }
});

// Auto-expand active sidebar collapse dropdown menu based on URL
document.addEventListener("DOMContentLoaded", function() {
    const currentPath = window.location.pathname;

    document.querySelectorAll(".sidebar .submenu-link").forEach(function(link) {
        const href = link.getAttribute("href");
        if (href && (currentPath === href || (href !== "/" && currentPath.startsWith(href)))) {
            link.classList.add("active");
            
            // Expand parent collapse container if inside dropdown
            const parentCollapse = link.closest(".collapse");
            if (parentCollapse) {
                parentCollapse.classList.add("show");
                const toggleBtn = document.querySelector(`[data-bs-target="#${parentCollapse.id}"]`);
                if (toggleBtn) {
                    toggleBtn.setAttribute("aria-expanded", "true");
                    toggleBtn.classList.add("active");
                }
            }
        }
    });

    // Check top-level nav links like Dashboard / Audit
    document.querySelectorAll(".sidebar > .nav-link").forEach(function(link) {
        const href = link.getAttribute("href");
        if (href && (currentPath === href || (href !== "/" && currentPath.startsWith(href)))) {
            link.classList.add("active");
        }
    });
});

// Initialize Dashboard Charts
document.addEventListener("DOMContentLoaded", function() {
    const fundChartCtx = document.getElementById("fundSourcesChart");
    if (fundChartCtx && typeof Chart !== "undefined") {
        new Chart(fundChartCtx, {
            type: 'doughnut',
            data: {
                labels: ['Youth Contribution', 'Village Contribution', 'Outside Donors', 'Previous Balance'],
                datasets: [{
                    data: [85000, 110000, 35000, 15000],
                    backgroundColor: ['#8b1e24', '#f4a261', '#e9c46a', '#2b2d42'],
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            font: { family: 'Inter', size: 12 },
                            usePointStyle: true,
                            padding: 16
                        }
                    }
                },
                cutout: '70%'
            }
        });
    }

    const expenseChartCtx = document.getElementById("expenseCategoriesChart");
    if (expenseChartCtx && typeof Chart !== "undefined") {
        new Chart(expenseChartCtx, {
            type: 'bar',
            data: {
                labels: ['Decorations', 'Annasantharpana', 'Poojas', 'Lighting', 'Sound System', 'Banners'],
                datasets: [{
                    label: 'Amount (₹)',
                    data: [28000, 35000, 12000, 15000, 8000, 4500],
                    backgroundColor: '#8b1e24',
                    borderRadius: 6,
                    maxBarThickness: 32
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { font: { family: 'Inter', size: 11 } }
                    },
                    y: {
                        grid: { color: '#f1f5f9' },
                        ticks: { font: { family: 'Inter', size: 11 } }
                    }
                }
            }
        });
    }
});

// Global Checkbox Selection & Bulk Toolbar Handler
document.addEventListener("change", function(e) {
    // Select All Checkbox Handler
    if (e.target && e.target.id === "selectAll") {
        const checkboxes = document.querySelectorAll(".row-checkbox");
        checkboxes.forEach(cb => cb.checked = e.target.checked);
        updateBulkToolbar();
    }
    
    // Row Checkbox Handler
    if (e.target && e.target.classList.contains("row-checkbox")) {
        const selectAll = document.getElementById("selectAll");
        const checkboxes = document.querySelectorAll(".row-checkbox");
        const checkedCount = document.querySelectorAll(".row-checkbox:checked").length;
        if (selectAll) {
            selectAll.checked = (checkedCount === checkboxes.length && checkboxes.length > 0);
        }
        updateBulkToolbar();
    }
});

function updateBulkToolbar() {
    const checkedCount = document.querySelectorAll(".row-checkbox:checked").length;
    const toolbar = document.getElementById("bulkActionsToolbar");
    const countBadge = document.getElementById("selectedCount");
    
    if (toolbar) {
        if (checkedCount > 0) {
            toolbar.classList.add("show");
            if (countBadge) countBadge.textContent = checkedCount;
        } else {
            toolbar.classList.remove("show");
        }
    }
}

// Trigger Print Dialog for Modal
function triggerPrint() {
    window.print();
}

// Client-Side Form Validation & Live Error Text Removal
document.addEventListener("submit", function(e) {
    const form = e.target;
    if (!form || form.tagName !== "FORM") return;

    let isFormValid = true;
    const requiredInputs = form.querySelectorAll("input[required], select[required], textarea[required]");

    requiredInputs.forEach(input => {
        const val = input.value ? input.value.trim() : "";
        let feedback = input.nextElementSibling;
        if (feedback && !feedback.classList.contains("invalid-feedback")) {
            feedback = input.parentElement.querySelector(".invalid-feedback");
        }

        if (!val) {
            isFormValid = false;
            input.classList.add("is-invalid");
            if (!feedback) {
                feedback = document.createElement("div");
                feedback.className = "invalid-feedback d-block text-danger small mt-1";
                feedback.innerHTML = "* This field is required";
                input.parentNode.appendChild(feedback);
            } else {
                feedback.style.display = "block";
                feedback.innerHTML = "* This field is required";
            }
        } else {
            input.classList.remove("is-invalid");
            if (feedback && feedback.classList.contains("invalid-feedback")) {
                feedback.style.display = "none";
            }
        }
    });

    if (!isFormValid) {
        e.preventDefault();
        e.stopPropagation();
    }
});

// Live input/change listener to hide error text per field as soon as user types or selects
document.addEventListener("input", handleLiveFieldValidation);
document.addEventListener("change", handleLiveFieldValidation);

function handleLiveFieldValidation(e) {
    const field = e.target;
    if (!field || !["INPUT", "SELECT", "TEXTAREA"].includes(field.tagName)) return;

    if (field.hasAttribute("required")) {
        const val = field.value ? field.value.trim() : "";
        let feedback = field.nextElementSibling;
        if (feedback && !feedback.classList.contains("invalid-feedback")) {
            feedback = field.parentElement.querySelector(".invalid-feedback");
        }

        if (val) {
            field.classList.remove("is-invalid");
            if (feedback && feedback.classList.contains("invalid-feedback")) {
                feedback.style.display = "none";
            }
        }
    }
}

