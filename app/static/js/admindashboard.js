document.addEventListener("DOMContentLoaded", function() {
    // Initialize the dashboard
    initDashboard();

    // Set up event listeners
    setupEventListeners();
    fetchFormVisibility()
    // Update status message with default visibility (0 = disabled)
    updateStatusMessage();
    fetchLoginActivity();
    // Fetch initial data
    getTotalEmployees();
    fetchAndPrefillEmpID();

    // Check for saved state and restore it
    restoreState();

    // Add overlay click handler to close expanded features
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('feature-expanded-view') && !e.target.classList.contains('hidden')) {
            const featureId = e.target.id.replace('View', '');
            collapseFeature(featureId);
        }
    });
});

// Initialize dashboard
function initDashboard() {
    // Set current date for greeting
    updateGreeting();

    // Initialize sidebar navigation
    initNavigation();

    // Add animation classes
    document.querySelectorAll('.feature-card').forEach(card => {
        card.classList.add('animate-in');
    });
}

// Update greeting based on time of day
function updateGreeting() {
    const greeting = document.querySelector('.greeting');
    const hour = new Date().getHours();
    let greetingText = 'Good ';

    if (hour < 12) {
        greetingText += 'Morning';
    } else if (hour < 18) {
        greetingText += 'Afternoon';
    } else {
        greetingText += 'Evening';
    }

    if (greeting) {
        greeting.textContent = `${greetingText}, Admin!`;
    }
}

// Initialize navigation
function initNavigation() {
    const featureCards = document.querySelectorAll('.feature-card');

    featureCards.forEach(card => {
        card.addEventListener('click', function(e) {
            const featureId = this.getAttribute('data-feature');

            // Skip expansion for toggleForm and handle toggle directly
            if (featureId === 'toggleForm') {
                // Only expand if the click wasn't on the toggle switch itself
                if (!e.target.closest('.toggle-switch')) {
                    e.stopPropagation();
                }
                return;
            }

            // If dashboard, show dashboard view
            if (featureId === 'dashboard') {
                showDashboard();
            } else {
                // Otherwise expand the feature
                expandFeature(featureId);
            }

            // Save state
            saveState(featureId);
        });
    });
}

// Set up event listeners
function setupEventListeners() {
    // Form toggle - direct toggle on dashboard
    const formToggle = document.getElementById('formToggle');
    if (formToggle) {
        formToggle.addEventListener('change', function(e) {
            e.stopPropagation(); // Prevent card click event
            handleFormToggle();
        });
    }

    // Make the toggle form card non-expandable
    const toggleFormCard = document.querySelector('.feature-card[data-feature="toggleForm"]');
    if (toggleFormCard) {
        toggleFormCard.style.cursor = 'default';
    }

    // Rest of the event listeners remain the same
    // Search input
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keyup', function(e) {
            if (e.key === 'Enter') {
                searchFeatures(this.value);
            }
        });
    }


    // Create user form
    const createUserForm = document.getElementById('createUserForm');
    if (createUserForm) {
        createUserForm.addEventListener('submit', handleCreateUser);
    }

    // Form responses form
    const formResponsesForm = document.getElementById('formResponsesForm');
    if (formResponsesForm) {
        formResponsesForm.addEventListener('submit', handleFormResponses);
    }

    // Download activity button
    const downloadActivityBtn = document.getElementById('downloadActivityBtn');
    if (downloadActivityBtn) {
        downloadActivityBtn.addEventListener('click', handleDownloadActivity);
    }

    // Find user button
    const findUserBtn = document.getElementById('findUserBtn');
    if (findUserBtn) {
        findUserBtn.addEventListener('click', searchEmployee);
    }

    // Modal close button
    const closeModalBtn = document.querySelector('.close-modal-btn');
    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', hideModal);
    }

    // Modal cancel button
    const modalCancel = document.getElementById('modal-cancel');
    if (modalCancel) {
        modalCancel.addEventListener('click', hideModal);
    }

    // Window click to close modal
    window.addEventListener('click', function(e) {
        const modal = document.getElementById('confirmModal');
        if (e.target === modal) {
            hideModal();
        }
    });


    // Close buttons for expanded features
    document.querySelectorAll('.close-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const featureView = this.closest('.feature-expanded-view');
            const featureId = featureView.id.replace('View', '');
            collapseFeature(featureId);
        });
    });
}


    // Hamburger menu
    const hamburgerMenu = document.getElementById('hamburgerMenu');
    const profileDropdown = document.getElementById('profileDropdown');

    if (hamburgerMenu && profileDropdown) {
        hamburgerMenu.addEventListener('click', function() {
            profileDropdown.classList.toggle('active');
        });

        document.addEventListener('click', function(e) {
            if (!hamburgerMenu.contains(e.target) && !profileDropdown.contains(e.target)) {
                profileDropdown.classList.remove('active');
            }
        });
    }



// Fetch form visibility
function fetchFormVisibility() {
    fetch("/get_form_visibility")
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const isVisible = data.is_visible === 1;
                const formToggle = document.getElementById('formToggle');
                if (formToggle) {
                    formToggle.checked = isVisible;
                    updateStatusMessage(isVisible ? 1 : 0);
                }
            } else {
                console.error("Failed to fetch visibility:", data.message);
            }
        })
        .catch(err => {
            console.error("Error fetching visibility:", err);
        });
}


// Update status message
function updateStatusMessage(visibility) {
    const statusMessage = document.getElementById("form-status-message");
    if (!statusMessage) return;

    // Clear previous content
    statusMessage.innerHTML = "";

    // Create badge element
    const badge = document.createElement("div");
    badge.classList.add("status-badge");

    if (visibility === 1) {
        badge.classList.add('status-connected');
        badge.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" fill="none"></circle>
                <path d="M9 12l2 2 4-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path>
            </svg>
            <span>Currently enabled</span>
        `;
    } else {
        badge.classList.add("status-disabled");
        badge.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" fill="none"></circle>
                <line x1="8" y1="16" x2="16" y2="8" stroke="currentColor" stroke-width="2" stroke-linecap="round"></line>
                <line x1="8" y1="8" x2="16" y2="16" stroke="currentColor" stroke-width="2" stroke-linecap="round"></line>
            </svg>
            <span>Currently Disabled</span>
        `;
    }

    statusMessage.appendChild(badge);
}

// Handle form toggle
function handleFormToggle() {
    const formToggle = document.getElementById('formToggle');
    const isCurrentlyEnabled = formToggle.checked;

    // Revert the toggle state until confirmed
    formToggle.checked = !isCurrentlyEnabled;

    // Show confirmation modal
    const modalTitle = document.getElementById('modal-title');
    const modalMessage = document.getElementById('modal-message');
    const confirmBtn = document.getElementById('modal-confirm');

    const actionText = isCurrentlyEnabled ? "enable" : "disable";

    modalTitle.textContent = "Confirm Action";
    modalMessage.textContent = `Are you sure you want to ${actionText} the form?`;

    // Button style adjustment
    confirmBtn.classList.toggle("danger-btn", !isCurrentlyEnabled);

    // Confirm action handler
    confirmBtn.onclick = () => {
        fetch("/admin/toggle-visibility", {
            method: "POST",
            headers: { "Content-Type": "application/json" }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const visibility = data.new_visibility;
                formToggle.checked = visibility === 1;
                updateStatusMessage(visibility);
                showToast(`Form has been ${visibility === 1 ? "enabled" : "disabled"}.`, 'success');
            } else {
                showToast("Something went wrong.", 'error');
            }
        })
        .catch(error => {
            console.error("Error:", error);
            showToast("Server Error: Unable to process request.", 'error');
        });

        hideModal();
    };

    showModal();
}

// Get total employees
function getTotalEmployees() {
    fetch("/admin/total-employees")
        .then(response => response.json())
        .then(data => {
            const employeeCount = document.getElementById("employee-count");
            if (employeeCount) {
                employeeCount.textContent = `Total Employees: ${data.total}`;
            }

            const tableBody = document.querySelector("#employeeTable tbody");
            if (tableBody) {
                tableBody.innerHTML = "";

                data.employees.forEach(emp => {
                    let row = `<tr>
                        <td>${emp.emp_id}</td>
                        <td>${emp.email}</td>
                        <td>${emp.status}</td>
                        <td>
                            <button class="action-btn" onclick="toggleStatus('${emp.emp_id}', '${emp.status}')">
                                ${emp.status === 'Active' ? 'Block' : 'Unblock'}
                            </button>
                        </td>
                    </tr>`;
                    tableBody.innerHTML += row;
                });
            }
        })
        .catch(error => console.error("Error:", error));
}

// Search employee
function searchEmployee() {
    const empId = document.getElementById("search_emp_id").value.trim();
    const email = document.getElementById("search_name").value.trim();

    const params = new URLSearchParams();
    if (empId) params.append("emp_id", empId);
    if (email) params.append("email", email);

    fetch(`/admin/total-employees?${params.toString()}`)
        .then(response => response.json())
        .then(data => {
            const employeeCount = document.getElementById("employee-count");
            if (employeeCount) {
                employeeCount.textContent = `Found Employees: ${data.total}`;
            }

            const tableBody = document.querySelector("#employeeTable tbody");
            if (tableBody) {
                tableBody.innerHTML = "";

                const noResults = document.getElementById("no-results");

                if (data.total === 0) {
                    if (noResults) noResults.classList.remove("hidden");
                } else {
                    if (noResults) noResults.classList.add("hidden");

                    data.employees.forEach(emp => {
                        let row = `<tr>
                            <td>${emp.emp_id}</td>
                            <td>${emp.email}</td>
                            <td>${emp.status}</td>
                            <td>
                                <button class="action-btn" onclick="toggleStatus('${emp.emp_id}', '${emp.status}')">
                                    ${emp.status === 'Active' ? 'Block' : 'Unblock'}
                                </button>
                            </td>
                        </tr>`;
                        tableBody.innerHTML += row;
                    });
                }
            }
        })
        .catch(error => console.error("Error:", error));
}

// Toggle employee status
window.toggleStatus = function(emp_id, currentStatus) {
    const newStatus = currentStatus === "Active" ? "Blocked" : "Active";

    fetch("/admin/toggle-status", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ emp_id, status: newStatus })
    })
    .then(response => response.json())
    .then(data => {
        showToast(data.message, data.success ? 'success' : 'error');
        searchEmployee();
    })
    .catch(error => {
        console.error("Error:", error);
        showToast("Server error occurred", 'error');
    });
};

// Load activity data
function fetchLoginActivity() {
    fetch("/api/login-activity")
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const tbody = document.getElementById("activityTableBody");
                tbody.innerHTML = ""; // clear old data
                data.data.forEach(row => {
                    const tr = document.createElement("tr");
                    tr.innerHTML = `
                        <td>${row.emp_id}</td>
                        <td>${row.email}</td>
                        <td>${row.login_time}</td>
                        <td>${row.logout_time || "—"}</td>
                    `;
                    tbody.appendChild(tr);
                });
            }
        })
        .catch(err => {
            console.error("Failed to fetch login activity:", err);
        });
}


// Refresh every 15 seconds
setInterval(fetchLoginActivity, 15000);

// Optional: Call on feature expand if it's collapsed by default
function expandFeature(name) {
    if (name === 'activity') {
        document.getElementById("activityView").classList.remove("hidden");
        fetchLoginActivity();
    }
}



function loadFilteredResponses() {
    const form = document.getElementById('formResponsesForm');
    const manager_name = form.querySelector('[name="manager_name"]').value.trim();
    const emp_id = form.querySelector('[name="emp_id"]').value.trim();
    const month = form.querySelector('[name="month"]').value;

    const params = new URLSearchParams();
    if (manager_name) params.append("manager_name", manager_name);
    if (emp_id) params.append("emp_id", emp_id);
    if (month) params.append("month", month);

    fetch(`/view_filtered_responses?${params.toString()}`)
        .then(res => res.json())
        .then(data => {
            const tbody = document.getElementById("responsesTableBody");
            tbody.innerHTML = "";

            if (data.success && data.responses.length > 0) {
                document.getElementById("no-responses").classList.add("hidden");

                data.responses.forEach(response => {
                    const tr = document.createElement("tr");


                    tr.innerHTML = `
                        <td>${response.emp_id || ""}</td>
                        <td>${response.name || ""}</td>
                        <td>${response.manager_name || ""}</td>
                        <td>${response.designation || ""}</td>
                    `;
                    tbody.appendChild(tr);
                });

            } else {
                document.getElementById("no-responses").classList.remove("hidden");
            }
        })
        .catch(err => {
            console.error("Error fetching responses:", err);
        });
}


// Load all responses initially on page/feature open


// Download filtered data
function downloadFilteredResponses() {
    const form = document.getElementById('formResponsesForm');
    const managerName = form.manager_name.value.trim();
    const empId = form.emp_id.value.trim();
    const month = form.month.value;

    let query = [];
    if (managerName) query.push(`manager_name=${encodeURIComponent(managerName)}`);
    if (empId) query.push(`emp_id=${encodeURIComponent(empId)}`);
    if (month) query.push(`month=${encodeURIComponent(month)}`);

    const queryString = query.length ? `?${query.join('&')}` : '';
    window.location.href = `/download_responses${queryString}`;
}




// Handle download activity
function handleDownloadActivity() {
    window.location.href = "/admin/download-activity";
}

// Handle create user
function handleCreateUser(e) {
    e.preventDefault();

    const form = document.getElementById("createUserForm");
    const formData = new FormData(form); // Automatically includes all form fields and file inputs

    fetch("/admin/create-user", {
        method: "POST",
        body: formData, // no Content-Type header!
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast("User created successfully", "success");
            form.reset();
            collapseFeature('createEmployee');
            getTotalEmployees();
        } else {
            showToast(data.message || "Error creating user", "error");
        }
    })
    .catch(error => {
        console.error("Error:", error);
        showToast("Server error creating user", "error");
    });
}

function fetchAndPrefillEmpID() {
    fetch("/admin/next-emp-id")
        .then(res => res.json())
        .then(data => {
            if (data.emp_id) {
                document.getElementById("emp_id").value = data.emp_id;
            }
        })
        .catch(err => {
            console.error("Failed to fetch emp_id:", err);
            showToast("Unable to fetch employee ID", "error");
        });
}



// Handle form responses
function handleFormResponses(e) {
    e.preventDefault();

    const managerName = document.getElementById("manager_name").value.trim();
    const empId = document.getElementById("emp_id").value.trim();
    const month = document.getElementById("month").value;

    // Basic validation
    if (empId && !empId.toLowerCase().startsWith('sv_')) {
        showToast("Employee ID must start with 'SV_'.", "error");
        return;
    }

    // Build query params
    const params = new URLSearchParams();
    if (managerName) params.append("manager", managerName);
    if (month) params.append("month", month);
    if (empId) params.append("emp_id", empId);

    // First check if records exist
    fetch(`/check_response_count?${params.toString()}`)
        .then(response => response.json())
        .then(data => {
            if (data.count === 0) {
                showToast("No matching responses found.", "warning");
            } else {
                // Proceed to download
                window.location.href = `/download_responses?${params.toString()}`;
            }
        })
        .catch(error => {
            console.error("Error:", error);
            showToast("Error checking responses", "error");
        });
}




function highlightSuggestion(items) {
    items.forEach((item, i) => {
        item.classList.toggle('active', i === activeIndex);
    });
}

// Show dashboard
function showDashboard() {
    // Add fade-out animation to expanded views
    const expandedViews = document.querySelectorAll('.feature-expanded-view:not(.hidden)');
    expandedViews.forEach(view => {
        view.style.opacity = '0';
        setTimeout(() => {
            view.classList.add('hidden');
            view.style.opacity = '';
        }, 300);
    });

    // Show dashboard content with fade-in animation
    const dashboardContent = document.getElementById('dashboardContent');
    if (dashboardContent) {
        dashboardContent.style.opacity = '0';
        dashboardContent.classList.remove('hidden');
        setTimeout(() => {
            dashboardContent.style.opacity = '1';
        }, 10);
    }
}

// Expand feature
function expandFeature(featureId) {
    // Add fade-out animation to dashboard
    const dashboardContent = document.getElementById('dashboardContent');
    if (dashboardContent) {
        dashboardContent.style.opacity = '0';
        setTimeout(() => {
            dashboardContent.classList.add('hidden');
            dashboardContent.style.opacity = '';
        }, 300);
    }

    // Hide all expanded views
    const expandedViews = document.querySelectorAll('.feature-expanded-view');
    expandedViews.forEach(view => {
        view.classList.add('hidden');
    });

    // Show the selected feature view with animation
    const featureView = document.getElementById(`${featureId}View`);
    if (featureView) {
        featureView.classList.remove('hidden');
    }

    // Save state
    saveState(featureId);
}

// Collapse feature
function collapseFeature(featureId) {
    // Add fade-out animation to feature view
    const featureView = document.getElementById(`${featureId}View`);
    if (featureView) {
        featureView.style.opacity = '0';
        setTimeout(() => {
            featureView.classList.add('hidden');
            featureView.style.opacity = '';
        }, 300);
    }

    // Show dashboard content with fade-in animation
    const dashboardContent = document.getElementById('dashboardContent');
    if (dashboardContent) {
        dashboardContent.style.opacity = '0';
        dashboardContent.classList.remove('hidden');
        setTimeout(() => {
            dashboardContent.style.opacity = '1';
        }, 10);
    }

    // Save state
    saveState('dashboard');
}

// Show modal
function showModal() {
    const modal = document.getElementById('confirmModal');
    if (modal) {
        modal.classList.add('active');
    }
}

// Hide modal
function hideModal() {
    const modal = document.getElementById('confirmModal');
    if (modal) {
        modal.classList.remove('active');
    }
}

// Show toast notification
function showToast(message, type = 'success') {
    // Remove existing toasts
    const existingToasts = document.querySelectorAll('.toast');
    existingToasts.forEach(toast => {
        document.body.removeChild(toast);
    });

    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;

    // Add to body
    document.body.appendChild(toast);

    // Show toast
    setTimeout(() => {
        toast.classList.add('show');

        // Hide toast after delay
        setTimeout(() => {
            toast.classList.remove('show');

            // Remove from DOM after animation
            setTimeout(() => {
                if (document.body.contains(toast)) {
                    document.body.removeChild(toast);
                }
            }, 300);
        }, 3000);
    }, 100);
}

// Save current state to localStorage
function saveState(featureId) {
    localStorage.setItem('currentFeature', featureId);
}

// Restore state from localStorage
function restoreState() {
    const currentFeature = localStorage.getItem('currentFeature');

    if (currentFeature) {
        if (currentFeature === 'dashboard') {
            showDashboard();
        } else {
            expandFeature(currentFeature);
        }
    }
}

window.addEventListener("load", function () {
  const loader = document.getElementById("loadingScreen");
  const main = document.getElementById("mainContent");

  if (loader) loader.style.display = "none";
  if (main) main.style.display = "block";
});



//logout
function handleLogout() {
    const logoutBtn = document.querySelector('.logout-btn');

    const modalTitle = document.getElementById('modal-title');
    const modalMessage = document.getElementById('modal-message');
    const confirmBtn = document.getElementById('modal-confirm');

    modalTitle.textContent = "Confirm Logout";
    modalMessage.textContent = "Are you sure you want to log out from your account?";

    // Optional: visually highlight danger
    confirmBtn.classList.add("danger-btn");

    // Set confirm action
    confirmBtn.onclick = () => {
        showToast("Logging out...", "success");
        window.location.href = "/logout";
    };

    showModal();
}

document.getElementById('excelUploadForm').addEventListener('submit', function (e) {
    e.preventDefault();

    const formData = new FormData(this);

    fetch('/upload_excel', {
        method: 'POST',
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        const category = data.success ? 'success' : 'error';
        showToast(data.message, category);

        if (data.success) {
            this.reset();  // Clear form if successful
        }
    })
    .catch(() => {
        showToast("Something went wrong while uploading the file.", "error");
    });
});
