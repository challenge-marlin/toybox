/**
 * エラーハンドリングと通知
 */

/**
 * Toast通知を表示
 * @param {string} type - 'success', 'error', 'info', 'warning'
 * @param {string} message - 表示メッセージ
 * @param {number} duration - 表示時間（ミリ秒）
 */
function showToast(type, message, duration = 3000) {
    // 既存のtoast関数がある場合はそれを使用
    if (typeof window.showToast === 'function') {
        window.showToast(type, message);
        return;
    }
    
    // 簡易的なToast実装
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed;
        top: 1rem;
        right: 1rem;
        padding: 1rem 1.5rem;
        border-radius: 4px;
        background: ${type === 'error' ? '#dc2626' : type === 'success' ? '#10b981' : '#3b82f6'};
        color: white;
        z-index: 10000;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        animation: slideIn 0.3s ease-out;
    `;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, duration);
}

/**
 * APIエラーを処理してメッセージを表示
 * @param {Error} error - エラーオブジェクト
 * @param {string} defaultMessage - デフォルトエラーメッセージ
 */
function handleApiError(error, defaultMessage = 'エラーが発生しました') {
    console.error('API Error:', error);
    
    let message = defaultMessage;
    
    if (error.message) {
        // HTTPエラーの場合
        if (error.message.includes('HTTP')) {
            const match = error.message.match(/HTTP (\d+):\s*(.+)/);
            if (match) {
                const status = match[1];
                const errorText = match[2];
                
                try {
                    const errorData = JSON.parse(errorText);
                    message = errorData.message || errorData.detail || errorData.error || message;
                } catch (e) {
                    message = errorText || message;
                }
            }
        } else {
            message = error.message;
        }
    }
    
    showToast('error', message);
    return message;
}

/**
 * エラーメッセージを表示（既存の要素に）
 * @param {HTMLElement} element - メッセージを表示する要素
 * @param {string} message - エラーメッセージ
 * @param {boolean} isError - エラーかどうか（true: エラー、false: 成功）
 */
function showMessage(element, message, isError = true) {
    if (!element) return;
    
    element.textContent = message;
    element.style.display = 'block';
    element.style.color = isError ? '#dc2626' : 'var(--steam-gold-300)';
}

/**
 * エラーメッセージを非表示
 * @param {HTMLElement} element - メッセージ要素
 */
function hideMessage(element) {
    if (!element) return;
    element.style.display = 'none';
}





