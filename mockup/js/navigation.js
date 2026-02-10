// AUREAVIA - Global Navigation & Utilities
// ==========================================

// Auth Management
// ==========================================

function checkAuth() {
    if (!localStorage.getItem('aureavia_logged')) {
        window.location.href = 'index.html';
    }
}

function logout() {
    showConfirmDialog(
        'Confirm Logout',
        'Are you sure you want to logout?',
        function() {
            localStorage.clear();
            window.location.href = 'index.html';
        }
    );
}

// Navigation
// ==========================================

function navigateTo(page) {
    window.location.href = page + '.html';
}

function goBack() {
    window.history.back();
}

// Menu Management
// ==========================================

let isMenuOpen = false;

function toggleMenu() {
    const dropdown = document.getElementById('dropdownMenu');
    if (dropdown) {
        dropdown.classList.toggle('hidden');
        isMenuOpen = !isMenuOpen;
    }
}

// Close menu when clicking outside
document.addEventListener('click', function(event) {
    const dropdown = document.getElementById('dropdownMenu');
    const headerUser = document.querySelector('.header-user');
    const mobileMenuBtn = document.querySelector('.mobile-menu-btn');

    if (dropdown && headerUser) {
        if (!headerUser.contains(event.target) &&
            !dropdown.contains(event.target) &&
            (!mobileMenuBtn || !mobileMenuBtn.contains(event.target))) {
            dropdown.classList.add('hidden');
            isMenuOpen = false;
        }
    }
});

// Tab Management (Rides List)
// ==========================================

function setActiveTab(tabName) {
    // Remove active class from all tabs
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => tab.classList.remove('active'));

    // Add active class to clicked tab
    const activeTab = document.querySelector(`[data-filter="${tabName}"]`);
    if (activeTab) {
        activeTab.classList.add('active');
    }

    // Filter ride cards
    const rideCards = document.querySelectorAll('.ride-card');
    rideCards.forEach(card => {
        const status = card.getAttribute('data-status');
        if (tabName === 'all') {
            card.style.display = 'block';
            card.classList.add('fade-in');
        } else if (tabName === status) {
            card.style.display = 'block';
            card.classList.add('fade-in');
        } else {
            card.style.display = 'none';
        }
    });
}

// Filter Management
// ==========================================

const activeFilters = {
    passengers: [],
    route: [],
    distance: []
};

function toggleFilter(filterType, value) {
    const chips = document.querySelectorAll(`[data-filter="${filterType}"][data-value="${value}"]`);

    chips.forEach(chip => {
        chip.classList.toggle('active');

        const index = activeFilters[filterType].indexOf(value);
        if (chip.classList.contains('active')) {
            if (index === -1) {
                activeFilters[filterType].push(value);
            }
        } else {
            if (index > -1) {
                activeFilters[filterType].splice(index, 1);
            }
        }
    });

    applyFilters();
}

function applyFilters() {
    const rideCards = document.querySelectorAll('.ride-card');
    const hasActiveFilters = Object.values(activeFilters).some(arr => arr.length > 0);

    // Get current tab filter
    const activeTab = document.querySelector('.tab.active');
    const tabFilter = activeTab ? activeTab.getAttribute('data-filter') : 'all';

    rideCards.forEach(card => {
        let shouldShow = true;

        // Apply tab filter first
        const status = card.getAttribute('data-status');
        if (tabFilter !== 'all' && status !== tabFilter) {
            shouldShow = false;
        }

        // Apply chip filters if any are active
        if (hasActiveFilters && shouldShow) {
            const distanceText = card.querySelector('.ride-distance span')?.textContent || '0';
            const distance = parseInt(distanceText);
            const passengers = parseInt(card.getAttribute('data-passengers'));
            const routeType = card.getAttribute('data-route');

            // Distance filter
            if (activeFilters.distance.length > 0) {
                let matchesDistance = false;
                activeFilters.distance.forEach(filter => {
                    if (filter === '<20' && distance < 20) matchesDistance = true;
                    if (filter === '20-50' && distance >= 20 && distance <= 50) matchesDistance = true;
                    if (filter === '>50' && distance > 50) matchesDistance = true;
                });
                if (!matchesDistance) shouldShow = false;
            }

            // Passengers filter
            if (activeFilters.passengers.length > 0) {
                let matchesPassengers = false;
                activeFilters.passengers.forEach(filter => {
                    if (filter === '1-2' && passengers >= 1 && passengers <= 2) matchesPassengers = true;
                    if (filter === '3-4' && passengers >= 3 && passengers <= 4) matchesPassengers = true;
                    if (filter === '5+' && passengers >= 5) matchesPassengers = true;
                });
                if (!matchesPassengers) shouldShow = false;
            }

            // Route type filter
            if (activeFilters.route.length > 0) {
                if (!activeFilters.route.includes(routeType)) {
                    shouldShow = false;
                }
            }
        }

        card.style.display = shouldShow ? 'block' : 'none';
        if (shouldShow) {
            card.classList.add('fade-in');
        }
    });
}

// Ride Selection
// ==========================================

function selectRide(rideId) {
    localStorage.setItem('selectedRide', rideId);
    window.location.href = 'ride-detail.html?id=' + rideId;
}

function viewRideDetails(event, rideId) {
    event.preventDefault();
    selectRide(rideId);
}

// Ride Actions
// ==========================================

function acceptRide() {
    const modal = document.getElementById('modalOverlay');
    if (modal) {
        modal.classList.add('active');
        modal.classList.add('fade-in');
    }
}

function declineRide() {
    showConfirmDialog(
        'Decline Ride',
        'Are you sure you want to decline this ride?',
        function() {
            showToast('Ride declined', 'info');
            setTimeout(() => {
                window.location.href = 'rides-list.html';
            }, 1000);
        }
    );
}

function closeModal() {
    window.location.href = 'rides-list.html';
}

function navigateToPickup() {
    const urlParams = new URLSearchParams(window.location.search);
    const rideId = urlParams.get('id') || '1';

    // Get pickup location from ride data
    const pickupLocations = {
        '1': 'Milano Centrale Station',
        '2': 'Via Montenapoleone 12, Milano',
        '3': 'Hotel Principe di Savoia, Milano',
        '4': 'Bergamo Airport',
        '5': 'Milano Porta Garibaldi',
        '6': 'Como Centro'
    };

    const pickup = pickupLocations[rideId] || 'Milano Centrale Station';
    const encodedPickup = encodeURIComponent(pickup);
    window.open('https://maps.google.com/?q=' + encodedPickup, '_blank');
}

function callPassenger() {
    window.location.href = 'tel:+393331234567';
}

// Toast Notifications
// ==========================================

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'toast toast-' + type + ' slide-in-right';

    const icons = {
        success: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>',
        error: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>',
        info: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>'
    };

    toast.innerHTML = `
        <div class="toast-icon">${icons[type]}</div>
        <div class="toast-message">${message}</div>
        <button class="toast-close" onclick="this.parentElement.remove()" aria-label="Close">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
        </button>
    `;

    container.appendChild(toast);

    // Auto remove after 3 seconds
    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Form Validation
// ==========================================

function validateEmail(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

function validatePassword(password) {
    return password.length >= 6;
}

function showFieldError(fieldId, message) {
    const field = document.getElementById(fieldId);
    if (!field) return;

    // Remove existing error
    const existingError = field.parentElement.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }

    // Add error message
    const error = document.createElement('div');
    error.className = 'field-error';
    error.textContent = message;
    field.parentElement.appendChild(error);

    // Add error class to input container
    const container = field.closest('.input-container');
    if (container) {
        container.classList.add('error');
    }
}

function clearFieldError(fieldId) {
    const field = document.getElementById(fieldId);
    if (!field) return;

    const error = field.parentElement.querySelector('.field-error');
    if (error) {
        error.remove();
    }

    const container = field.closest('.input-container');
    if (container) {
        container.classList.remove('error');
    }
}

// Loading States
// ==========================================

function showButtonLoading(buttonElement, loadingText = 'Loading...') {
    if (!buttonElement) return;

    buttonElement.disabled = true;
    buttonElement.style.opacity = '0.6';
    buttonElement.setAttribute('data-original-text', buttonElement.textContent);

    buttonElement.innerHTML = `
        <svg class="spinner" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        ${loadingText}
    `;
}

function hideButtonLoading(buttonElement) {
    if (!buttonElement) return;

    buttonElement.disabled = false;
    buttonElement.style.opacity = '1';
    const originalText = buttonElement.getAttribute('data-original-text');
    if (originalText) {
        buttonElement.textContent = originalText;
    }
}

// Login Form Handler
// ==========================================

function handleLogin(event) {
    event.preventDefault();

    const emailField = document.getElementById('email');
    const passwordField = document.getElementById('password');
    const submitButton = event.target.querySelector('button[type="submit"]');

    if (!emailField || !passwordField) return;

    const email = emailField.value.trim();
    const password = passwordField.value.trim();

    // Clear previous errors
    clearFieldError('email');
    clearFieldError('password');

    let hasError = false;

    // Validate email
    if (!email) {
        showFieldError('email', 'Email is required');
        hasError = true;
    } else if (!validateEmail(email)) {
        showFieldError('email', 'Please enter a valid email address');
        hasError = true;
    }

    // Validate password
    if (!password) {
        showFieldError('password', 'Password is required');
        hasError = true;
    } else if (!validatePassword(password)) {
        showFieldError('password', 'Password must be at least 6 characters');
        hasError = true;
    }

    if (hasError) return;

    // Show loading state
    showButtonLoading(submitButton, 'Logging in...');

    // Simulate API call
    setTimeout(() => {
        localStorage.setItem('aureavia_logged', 'true');
        localStorage.setItem('aureavia_user', JSON.stringify({
            name: 'Marco Rossi',
            email: email,
            role: 'driver'
        }));

        window.location.href = 'rides-list.html';
    }, 1000);
}

// Mobile Menu
// ==========================================

function toggleMobileMenu() {
    const backdrop = document.getElementById('mobileMenuBackdrop');
    const menu = document.getElementById('mobileMenuPanel');

    if (backdrop && menu) {
        backdrop.classList.toggle('active');
        menu.classList.toggle('active');
        document.body.style.overflow = backdrop.classList.contains('active') ? 'hidden' : '';
    }
}

function closeMobileMenu() {
    const backdrop = document.getElementById('mobileMenuBackdrop');
    const menu = document.getElementById('mobileMenuPanel');

    if (backdrop && menu) {
        backdrop.classList.remove('active');
        menu.classList.remove('active');
        document.body.style.overflow = '';
    }
}

// Utility Functions
// ==========================================

function goToRides() {
    window.location.href = 'rides-list.html';
}

function editVehicle() {
    showToast('Feature coming soon', 'info');
}

function changePassword() {
    showToast('Feature coming soon', 'info');
}

// Initialize on page load
// ==========================================

document.addEventListener('DOMContentLoaded', function() {
    // Add fade-in animation to main content
    const content = document.querySelector('.content, .rides-container');
    if (content) {
        content.classList.add('fade-in');
    }

    // Initialize tooltips, if any
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(element => {
        element.setAttribute('aria-label', element.getAttribute('data-tooltip'));
    });
});

// Confirmation Dialog
// ==========================================

function showConfirmDialog(title, message, onConfirm) {
    const overlay = document.createElement('div');
    overlay.className = 'confirm-overlay';
    overlay.innerHTML = `
        <div class="confirm-dialog scale-in">
            <h3 class="confirm-title">${title}</h3>
            <p class="confirm-message">${message}</p>
            <div class="confirm-actions">
                <button class="confirm-btn confirm-btn-cancel" onclick="this.closest('.confirm-overlay').remove()">
                    Cancel
                </button>
                <button class="confirm-btn confirm-btn-confirm" id="confirmButton">
                    Confirm
                </button>
            </div>
        </div>
    `;

    document.body.appendChild(overlay);

    // Add confirm handler
    document.getElementById('confirmButton').addEventListener('click', function() {
        overlay.remove();
        if (onConfirm) onConfirm();
    });

    // Close on overlay click
    overlay.addEventListener('click', function(e) {
        if (e.target === overlay) {
            overlay.remove();
        }
    });
}

// Keyboard Navigation
// ==========================================

document.addEventListener('keydown', function(event) {
    // ESC key closes modals and menus
    if (event.key === 'Escape') {
        const modal = document.getElementById('modalOverlay');
        if (modal && modal.classList.contains('active')) {
            modal.classList.remove('active');
        }

        const dropdown = document.getElementById('dropdownMenu');
        if (dropdown && !dropdown.classList.contains('hidden')) {
            dropdown.classList.add('hidden');
        }

        closeMobileMenu();

        // Close confirm dialogs
        const confirmOverlay = document.querySelector('.confirm-overlay');
        if (confirmOverlay) {
            confirmOverlay.remove();
        }
    }
});