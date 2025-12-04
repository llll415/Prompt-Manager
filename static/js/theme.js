//全局主题切换逻辑
(function() {
    // 1. 立即执行：在 DOM 加载前尽快设置主题，避免闪烁
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);

    // 2. 暴露全局切换函数
    window.toggleTheme = function() {
        const current = document.documentElement.getAttribute('data-theme');
        const target = current === 'dark' ? 'light' : 'dark';
        
        document.documentElement.setAttribute('data-theme', target);
        localStorage.setItem('theme', target);
        
        updateThemeIcon(target);
    };

    // 3. 辅助函数：更新图标状态
    function updateThemeIcon(theme) {
        const icon = document.getElementById('themeIcon');
        if(icon) {
            icon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-stars-fill';
        }
    }

    // 4. DOM 加载完成后，确保图标状态正确
    document.addEventListener("DOMContentLoaded", function() {
        updateThemeIcon(savedTheme);
    });
})();