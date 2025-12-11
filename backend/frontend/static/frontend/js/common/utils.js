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

/**
 * URLを検出する正規表現
 * http://, https://, www., ドメイン名（.com, .jp等）を含むパターンを検出
 */
function detectURL(text) {
    if (!text) return false;
    
    // URLパターン: http://, https://, www., ドメイン名（.com, .jp, .net等）
    const urlPatterns = [
        /https?:\/\//i,           // http:// または https://
        /www\./i,                  // www.
        /[a-zA-Z0-9-]+\.[a-zA-Z]{2,}/,  // ドメイン名（example.com, example.jp等）
        /\.(com|net|org|jp|co\.jp|io|dev|app|xyz|info|biz|tv|me|cc|ws|mobi|asia|tel|name|pro|travel|museum|aero|coop|jobs|gov|edu|mil|int|ac|ad|ae|af|ag|ai|al|am|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cu|cv|cw|cx|cy|cz|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tr|tt|tv|tw|tz|ua|ug|uk|um|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|za|zm|zw)\b/i
    ];
    
    return urlPatterns.some(pattern => pattern.test(text));
}

/**
 * テキスト入力欄にURL検出機能を追加
 * @param {HTMLElement} inputElement - 入力要素（inputまたはtextarea）
 * @param {HTMLElement} errorElement - エラーメッセージを表示する要素（オプション）
 */
function setupURLValidation(inputElement, errorElement = null) {
    if (!inputElement) return;
    
    // エラー表示用の要素が指定されていない場合、入力欄の下に作成
    if (!errorElement) {
        errorElement = document.createElement('div');
        errorElement.style.cssText = 'font-size: 0.75rem; color: #dc2626; margin-top: 0.25rem; display: none;';
        errorElement.className = 'url-validation-error';
        
        // 親要素が存在する場合のみ挿入
        if (inputElement.parentNode) {
            // nextSiblingが存在する場合はその前に、存在しない場合は親要素の最後に追加
            if (inputElement.nextSibling) {
                inputElement.parentNode.insertBefore(errorElement, inputElement.nextSibling);
            } else {
                inputElement.parentNode.appendChild(errorElement);
            }
        } else {
            // 親要素が存在しない場合は、エラー要素を入力要素のデータ属性に保存しておく
            // 親要素が追加された後にエラー要素を挿入する
            inputElement.dataset.urlValidationError = 'pending';
            inputElement._urlValidationErrorElement = errorElement;
            
            // MutationObserverで親要素の追加を監視
            const observer = new MutationObserver(function(mutations) {
                if (inputElement.parentNode && inputElement.dataset.urlValidationError === 'pending') {
                    if (inputElement.nextSibling) {
                        inputElement.parentNode.insertBefore(errorElement, inputElement.nextSibling);
                    } else {
                        inputElement.parentNode.appendChild(errorElement);
                    }
                    inputElement.dataset.urlValidationError = 'added';
                    observer.disconnect();
                }
            });
            observer.observe(document.body, { childList: true, subtree: true });
            
            // タイムアウトで監視を停止（10秒後）
            setTimeout(() => {
                observer.disconnect();
            }, 10000);
        }
    }
    
    const showError = () => {
        errorElement.textContent = 'URL等のリンクは入力できません';
        errorElement.style.display = 'block';
        inputElement.style.borderColor = '#dc2626';
        inputElement.style.backgroundColor = 'rgba(220, 38, 38, 0.1)';
    };
    
    const hideError = () => {
        errorElement.style.display = 'none';
        inputElement.style.borderColor = '';
        inputElement.style.backgroundColor = '';
    };
    
    // 入力時の検証
    inputElement.addEventListener('input', function(e) {
        const value = e.target.value;
        if (detectURL(value)) {
            showError();
            // URL部分を削除
            const cleanedValue = value
                .replace(/https?:\/\/[^\s]+/gi, '')
                .replace(/www\.[^\s]+/gi, '')
                .replace(/[a-zA-Z0-9-]+\.[a-zA-Z]{2,}[^\s]*/gi, '')
                .trim();
            e.target.value = cleanedValue;
            // フォーカスを維持して再入力を促す
            setTimeout(() => {
                e.target.focus();
            }, 10);
        } else {
            hideError();
        }
    });
    
    // フォーカスアウト時の検証
    inputElement.addEventListener('blur', function(e) {
        const value = e.target.value;
        if (detectURL(value)) {
            showError();
        } else {
            hideError();
        }
    });
    
    // 貼り付け時の検証
    inputElement.addEventListener('paste', function(e) {
        setTimeout(() => {
            const value = e.target.value;
            if (detectURL(value)) {
                showError();
                const cleanedValue = value
                    .replace(/https?:\/\/[^\s]+/gi, '')
                    .replace(/www\.[^\s]+/gi, '')
                    .replace(/[a-zA-Z0-9-]+\.[a-zA-Z]{2,}[^\s]*/gi, '')
                    .trim();
                e.target.value = cleanedValue;
                e.target.focus();
            } else {
                hideError();
            }
        }, 10);
    });
}






