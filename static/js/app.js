// Mobile Sidebar Toggle
document.getElementById("menuBtn")?.addEventListener("click", function() {
    document.getElementById("sidebar")?.classList.toggle("show");
});

// Close sidebar on overlay click for mobile
document.addEventListener("click", function(e) {
    const sidebar = document.getElementById("sidebar");
    const menuBtn = document.getElementById("menuBtn");
    if (window.innerWidth < 992 && sidebar && sidebar.classList.contains("show")) {
        if (!sidebar.contains(e.target) && !menuBtn.contains(e.target)) {
            sidebar.classList.remove("show");
        }
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
