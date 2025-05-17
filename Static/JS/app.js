// Main Application JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Sidebar Elements
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const closeSidebar = document.getElementById('close-sidebar');
    const sidebarOverlay = document.getElementById('sidebar-overlay');
    
    // Initialize sidebar overlay if it doesn't exist
    if (!sidebarOverlay) {
        const overlay = document.createElement('div');
        overlay.id = 'sidebar-overlay';
        overlay.className = 'sidebar-overlay';
        document.body.appendChild(overlay);
    }
    
    // Toggle Sidebar Function
    function toggleSidebar() {
        sidebar.classList.toggle('active');
        document.querySelector('.sidebar-overlay').classList.toggle('active');
        document.body.style.overflow = sidebar.classList.contains('active') ? 'hidden' : '';
    }
    
    // Close Sidebar Function
    function closeSidebarFunc() {
        sidebar.classList.remove('active');
        document.querySelector('.sidebar-overlay').classList.remove('active');
        document.body.style.overflow = '';
        mainContent.classList.remove('with-sidebar');
        dashboardContent.classList.remove('with-sidebar');
    }
    
    // Event Listeners
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function(e) {
            e.stopPropagation();
            toggleSidebar();
        });
    }
    
    if (closeSidebar) {
        closeSidebar.addEventListener('click', closeSidebarFunc);
    }
    
    // Close sidebar when clicking outside or on overlay
    document.addEventListener('click', function(e) {
        if (!sidebar.contains(e.target) && 
            e.target !== sidebarToggle && 
            !sidebarToggle.contains(e.target)) {
            closeSidebarFunc();
        }
    });
    
    // Prevent closing when clicking inside sidebar
    sidebar.addEventListener('click', function(e) {
        e.stopPropagation();
    });
    
    // Close sidebar when pressing Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && sidebar.classList.contains('active')) {
            closeSidebarFunc();
        }
    });
    
    // Handle window resize
    function handleResize() {
        if (window.innerWidth > 1200) {
            closeSidebarFunc();
        }
    }
    
    window.addEventListener('resize', handleResize);
    
    // Add active class to current page in navigation
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-links a');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.parentElement.classList.add('active');
        }
        
        // Add click handler for smooth transitions
        link.addEventListener('click', function(e) {
            // In a real app, you would handle navigation here
            // For now, we'll just update the active state
            navLinks.forEach(l => l.parentElement.classList.remove('active'));
            this.parentElement.classList.add('active');
            closeSidebarFunc();
        });
    });
    
    // Add transaction button
    const addBtn = document.getElementById('addTransactionBtn');
    if (addBtn) {
        addBtn.addEventListener('click', function() {
            // In a real app, this would open a form
            alert('Add transaction form would open here');
        });
    }
});
