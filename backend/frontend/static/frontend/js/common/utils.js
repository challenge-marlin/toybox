/**
 * 汎用ユーティリティ関数
 */

/**
 * 日付をフォーマット
 * @param {Date|string} date - 日付オブジェクトまたは文字列
 * @param {string} format - フォーマット（'ja-JP'など）
 * @returns {string}
 */
function formatDate(date, format = 'ja-JP') {
    if (!date) return '';
    
    const d = date instanceof Date ? date : new Date(date);
    if (isNaN(d.getTime())) return '';
    
    return d.toLocaleDateString(format, {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

/**
 * 日時をフォーマット
 * @param {Date|string} date - 日付オブジェクトまたは文字列
 * @param {string} format - フォーマット（'ja-JP'など）
 * @returns {string}
 */
function formatDateTime(date, format = 'ja-JP') {
    if (!date) return '';
    
    const d = date instanceof Date ? date : new Date(date);
    if (isNaN(d.getTime())) return '';
    
    return d.toLocaleString(format, {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * 相対時間を表示（例: "3時間前"）
 * @param {Date|string} date - 日付オブジェクトまたは文字列
 * @returns {string}
 */
function formatRelativeTime(date) {
    if (!date) return '';
    
    const d = date instanceof Date ? date : new Date(date);
    if (isNaN(d.getTime())) return '';
    
    const now = new Date();
    const diff = now - d;
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) return `${days}日前`;
    if (hours > 0) return `${hours}時間前`;
    if (minutes > 0) return `${minutes}分前`;
    return 'たった今';
}

/**
 * 文字数をカウントして表示要素を更新
 * @param {HTMLElement} input - 入力要素
 * @param {HTMLElement} counter - カウンター要素
 * @param {number} maxLength - 最大文字数
 */
function setupCharCounter(input, counter, maxLength) {
    if (!input || !counter) return;
    
    const updateCounter = () => {
        const length = input.value.length;
        counter.textContent = `${length}/${maxLength}`;
        
        // 最大文字数に近づいたら警告色に
        if (length > maxLength * 0.9) {
            counter.style.color = '#dc2626';
        } else {
            counter.style.color = 'var(--steam-iron-300)';
        }
    };
    
    input.addEventListener('input', updateCounter);
    updateCounter(); // 初期表示
}

/**
 * ファイルプレビューを作成
 * @param {File} file - ファイルオブジェクト
 * @param {HTMLElement} container - プレビューを表示するコンテナ
 * @param {string} type - 'image' または 'video'
 * @returns {string} - プレビューURL（revoke用）
 */
function createFilePreview(file, container, type = 'image') {
    if (!file || !container) return null;
    
    const url = URL.createObjectURL(file);
    
    if (type === 'image') {
        container.innerHTML = `<img src="${url}" alt="preview" style="width: 100%; height: 100%; object-fit: cover;">`;
    } else if (type === 'video') {
        container.innerHTML = `<video src="${url}" controls style="width: 100%; height: 100%; object-fit: contain;"></video>`;
    }
    
    return url;
}

/**
 * プレビューURLを解放
 * @param {string} url - プレビューURL
 */
function revokeFilePreview(url) {
    if (url) {
        URL.revokeObjectURL(url);
    }
}

/**
 * ローディング状態を設定
 * @param {HTMLElement} button - ボタン要素
 * @param {boolean} isLoading - ローディング中かどうか
 * @param {string} loadingText - ローディング中のテキスト
 * @param {string} normalText - 通常のテキスト
 */
function setLoadingState(button, isLoading, loadingText = '処理中…', normalText = '送信') {
    if (!button) return;
    
    button.disabled = isLoading;
    button.textContent = isLoading ? loadingText : normalText;
}

/**
 * ページ遷移前に確認ダイアログを表示
 * @param {string} message - 確認メッセージ
 * @returns {boolean} - ユーザーがOKを選択した場合true
 */
function confirmNavigation(message = '変更が保存されていません。本当に移動しますか？') {
    return window.confirm(message);
}

/**
 * ローカルストレージに強制リロードフラグを設定
 * @param {string} page - ページ識別子
 */
function setForceReloadFlag(page) {
    localStorage.setItem(`toybox_${page}_force_reload`, '1');
}

/**
 * 強制リロードフラグをチェックしてリロード
 * @param {string} page - ページ識別子
 */
function checkForceReloadFlag(page) {
    const flag = localStorage.getItem(`toybox_${page}_force_reload`);
    if (flag === '1') {
        localStorage.removeItem(`toybox_${page}_force_reload`);
        window.location.reload();
    }
}





