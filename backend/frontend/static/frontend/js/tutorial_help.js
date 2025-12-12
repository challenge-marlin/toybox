/**
 * チュートリアルヘルプポップオーバーの制御
 */

(function() {
    'use strict';
    
    let popoverOpen = false;
    
    function initTutorialHelp() {
        const btn = document.getElementById('tutorialHelpBtn');
        const popover = document.getElementById('tutorialHelpPopover');
        
        if (!btn || !popover) {
            return;
        }
        
        // ボタンクリックでポップオーバーを開閉
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            togglePopover();
        });
        
        // 外側クリックで閉じる
        document.addEventListener('click', function(e) {
            if (popoverOpen && !popover.contains(e.target) && !btn.contains(e.target)) {
                closePopover();
            }
        });
        
        // ESCキーで閉じる
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && popoverOpen) {
                closePopover();
            }
        });
        
        // ポップオーバー内のリンククリック時は閉じない（遷移するため）
        const links = popover.querySelectorAll('.tutorial-help-link');
        links.forEach(function(link) {
            link.addEventListener('click', function() {
                // リンククリック時は閉じる（遷移するため）
                closePopover();
            });
        });
    }
    
    function togglePopover() {
        const popover = document.getElementById('tutorialHelpPopover');
        const btn = document.getElementById('tutorialHelpBtn');
        
        if (!popover || !btn) {
            return;
        }
        
        if (popoverOpen) {
            closePopover();
        } else {
            openPopover();
        }
    }
    
    function openPopover() {
        const popover = document.getElementById('tutorialHelpPopover');
        const btn = document.getElementById('tutorialHelpBtn');
        
        if (!popover || !btn) {
            return;
        }
        
        popover.classList.add('show');
        popover.setAttribute('hidden', 'false');
        btn.setAttribute('aria-expanded', 'true');
        popoverOpen = true;
    }
    
    function closePopover() {
        const popover = document.getElementById('tutorialHelpPopover');
        const btn = document.getElementById('tutorialHelpBtn');
        
        if (!popover || !btn) {
            return;
        }
        
        popover.classList.remove('show');
        popover.setAttribute('hidden', 'true');
        btn.setAttribute('aria-expanded', 'false');
        popoverOpen = false;
    }
    
    // DOMContentLoaded時に初期化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initTutorialHelp);
    } else {
        initTutorialHelp();
    }
})();

