/**
 * プロフィール設定ページのJavaScript
 * Version: 2.0.1
 * Updated: 2026-01-14 - Refactored for better maintainability
 * Fixed: 2026-01-14 - Improved getFunction robustness for hideMessage
 * Fixed: 2026-01-14 - Fixed hideMessage is not defined error
 */

(function() {
    'use strict';
    
    // ============================================================================
    // 定数定義
    // ============================================================================
    const VALIDATION = {
        DISPLAY_NAME_MIN: 1,
        DISPLAY_NAME_MAX: 50,
        BIO_MAX: 1000
    };
    
    const SELECTORS = {
        SAVE_BUTTON: 'save-button',
        MESSAGE_DIV: 'message',
        DISPLAY_NAME_INPUT: 'display-name-input',
        BIO_INPUT: 'bio-input',
        BIO_COUNT: 'bio-count',
        HEADER_PREVIEW: 'header-preview',
        AVATAR_PREVIEW: 'avatar-preview',
        HEADER_INPUT: 'header-input',
        AVATAR_INPUT: 'avatar-input',
        DELETE_HEADER_BTN: 'delete-header-btn',
        DELETE_AVATAR_BTN: 'delete-avatar-btn'
    };
    
    // ============================================================================
    // 状態管理
    // ============================================================================
    let headerFile = null;
    let avatarFile = null;
    let headerPreviewUrl = null;
    let avatarPreviewUrl = null;
    
    // ============================================================================
    // ユーティリティ関数（フォールバック）
    // ============================================================================
    
    /**
     * 認証トークンを取得
     */
    function getAuthToken() {
        return typeof getAccessToken !== 'undefined' ? getAccessToken() : (localStorage.getItem('access_token') || '');
    }
    
    /**
     * CSRFトークンを取得
     */
    function getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }
    
    /**
     * 認証ヘッダーを作成
     */
    function createAuthHeaders(contentType = 'application/json') {
        const headers = {};
        const token = getAuthToken();
        const csrftoken = getCsrfToken();
        
        if (contentType) {
            headers['Content-Type'] = contentType;
        }
        
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        if (csrftoken) {
            headers['X-CSRFToken'] = csrftoken;
        }
        
        return headers;
    }
    
    /**
     * 401エラー時の処理
     */
    function handleUnauthorized() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login/';
        throw new Error('認証が必要です');
    }
    
    /**
     * ファイルプレビュー作成（utils.jsが読み込まれていない場合のフォールバック）
     */
    function createFilePreviewFallback(file, container, type = 'image') {
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
     * プレビューURL解放（utils.jsが読み込まれていない場合のフォールバック）
     */
    function revokeFilePreviewFallback(url) {
        if (url) {
            URL.revokeObjectURL(url);
        }
    }
    
    /**
     * ローディング状態設定（utils.jsが読み込まれていない場合のフォールバック）
     */
    function setLoadingStateFallback(button, isLoading, loadingText = '処理中…', normalText = '送信') {
        if (!button) return;
        button.disabled = isLoading;
        button.textContent = isLoading ? loadingText : normalText;
    }
    
    /**
     * メッセージ表示（utils.jsが読み込まれていない場合のフォールバック）
     */
    function showMessageFallback(element, message, isError = false) {
        if (!element) return;
        element.textContent = message;
        element.style.display = 'block';
        element.style.color = isError ? '#dc2626' : 'var(--steam-gold-300)';
    }
    
    /**
     * メッセージ非表示（utils.jsが読み込まれていない場合のフォールバック）
     */
    function hideMessageFallback(element) {
        if (!element) return;
        element.style.display = 'none';
    }
    
    /**
     * 文字数カウンター設定（utils.jsが読み込まれていない場合のフォールバック）
     */
    function setupCharCounterFallback(input, counter, maxLength) {
        if (!input || !counter) return;
        
        const updateCounter = () => {
            const length = input.value.length;
            counter.textContent = `${length}/${maxLength}`;
            counter.style.color = length > maxLength * 0.9 ? '#dc2626' : 'var(--steam-iron-300)';
        };
        
        input.addEventListener('input', updateCounter);
        updateCounter();
    }
    
    /**
     * URL検証設定（utils.jsが読み込まれていない場合のフォールバック）
     */
    function setupURLValidationFallback(inputElement, errorElement = null) {
        if (!inputElement) return;
        
        const detectURL = (text) => {
            if (!text) return false;
            return /https?:\/\//i.test(text) || /www\./i.test(text) || /[a-zA-Z0-9-]+\.[a-zA-Z]{2,}/.test(text);
        };
        
        if (!errorElement) {
            errorElement = document.createElement('div');
            errorElement.style.cssText = 'font-size: 0.75rem; color: #dc2626; margin-top: 0.25rem; display: none;';
            errorElement.className = 'url-validation-error';
            
            if (inputElement.parentNode) {
                inputElement.parentNode.insertBefore(errorElement, inputElement.nextSibling || null);
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
        
        const cleanURL = (value) => {
            return value
                .replace(/https?:\/\/[^\s]+/gi, '')
                .replace(/www\.[^\s]+/gi, '')
                .replace(/[a-zA-Z0-9-]+\.[a-zA-Z]{2,}[^\s]*/gi, '')
                .trim();
        };
        
        const validateAndClean = (e) => {
            const value = e.target.value;
            if (detectURL(value)) {
                showError();
                e.target.value = cleanURL(value);
                setTimeout(() => e.target.focus(), 10);
            } else {
                hideError();
            }
        };
        
        inputElement.addEventListener('input', validateAndClean);
        inputElement.addEventListener('blur', (e) => {
            if (detectURL(e.target.value)) {
                showError();
            } else {
                hideError();
            }
        });
        inputElement.addEventListener('paste', (e) => {
            setTimeout(() => validateAndClean(e), 10);
        });
    }
    
    // ============================================================================
    // API呼び出しヘルパー（フォールバック）
    // ============================================================================
    
    /**
     * API GET呼び出しヘルパー
     */
    async function apiGetFallback(url) {
        const response = await fetch(url, {
            method: 'GET',
            headers: createAuthHeaders()
        });
        
        if (response.status === 401) {
            handleUnauthorized();
        }
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }
        
        return await response.json();
    }
    
    /**
     * API POST呼び出しヘルパー
     */
    async function apiPostFallback(url, data) {
        const isFormData = data instanceof FormData;
        const headers = createAuthHeaders(isFormData ? null : 'application/json');
        const body = isFormData ? data : JSON.stringify(data);
        
        const response = await fetch(url, {
            method: 'POST',
            headers: headers,
            body: body
        });
        
        if (response.status === 401) {
            handleUnauthorized();
        }
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }
        
        return await response.json();
    }
    
    /**
     * API PATCH呼び出しヘルパー
     */
    async function apiPatchFallback(url, data) {
        const response = await fetch(url, {
            method: 'PATCH',
            headers: createAuthHeaders(),
            body: JSON.stringify(data)
        });
        
        if (response.status === 401) {
            handleUnauthorized();
        }
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }
        
        return await response.json();
    }
    
    /**
     * API DELETE呼び出しヘルパー
     */
    async function apiDeleteFallback(url) {
        const response = await fetch(url, {
            method: 'DELETE',
            headers: createAuthHeaders(null)
        });
        
        if (response.status === 401) {
            handleUnauthorized();
        }
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }
        
        const text = await response.text();
        return text ? JSON.parse(text) : {};
    }
    
    // ============================================================================
    // ヘルパー関数
    // ============================================================================
    
    /**
     * 関数の存在チェックとフォールバック取得
     */
    function getFunction(globalFunc, fallbackFunc) {
        if (typeof globalFunc !== 'undefined' && typeof globalFunc === 'function') {
            return globalFunc;
        }
        return fallbackFunc;
    }
    
    /**
     * エラーハンドリング
     */
    function handleError(error, message) {
        const handleErrorFunc = getFunction(handleApiError, (err, msg) => {
            console.error(msg, err);
            return msg + ': ' + err.message;
        });
        return handleErrorFunc(error, message);
    }
    
    /**
     * プレビューをクリア
     */
    function clearPreview(type) {
        const revokeFunc = getFunction(revokeFilePreview, revokeFilePreviewFallback);
        
        if (type === 'header') {
            if (headerPreviewUrl) {
                revokeFunc(headerPreviewUrl);
                headerPreviewUrl = null;
            }
            headerFile = null;
        } else if (type === 'avatar') {
            if (avatarPreviewUrl) {
                revokeFunc(avatarPreviewUrl);
                avatarPreviewUrl = null;
            }
            avatarFile = null;
        }
    }
    
    /**
     * 画像アップロード処理
     */
    async function uploadImage(type) {
        const file = type === 'header' ? headerFile : avatarFile;
        if (!file) return;
        
        const apiPostFunc = getFunction(apiPost, apiPostFallback);
        const formData = new FormData();
        formData.append('file', file);
        
        console.log(`Uploading ${type} image...`, file);
        
        try {
            const result = await apiPostFunc(`/api/user/profile/upload/?type=${type}`, formData);
            console.log(`${type} upload result:`, result);
            
            const urlField = type === 'header' ? 'headerUrl' : 'avatarUrl';
            if (!result.ok && !result[urlField]) {
                throw new Error(`${type === 'header' ? 'ヘッダー' : 'アバター'}画像のアップロードに失敗しました`);
            }
            
            clearPreview(type);
            return result;
        } catch (error) {
            console.error(`${type} upload error:`, error);
            throw new Error(`${type === 'header' ? 'ヘッダー' : 'アバター'}画像のアップロードに失敗しました: ${error.message}`);
        }
    }
    
    /**
     * アバター画像のHTMLを生成
     */
    function createAvatarHTML(avatarUrl, displayName) {
        const firstChar = (displayName || 'U').charAt(0).toUpperCase();
        const fallbackHTML = `<span style="display: flex; align-items: center; justify-content: center; height: 100%; width: 100%; background: var(--steam-iron-800); color: var(--steam-gold-300); font-size: 1.5rem; font-weight: 600;">${firstChar}</span>`;
        
        if (avatarUrl) {
            return `<img src="${avatarUrl}" alt="avatar" onerror="this.style.display='none'; this.parentElement.innerHTML='${fallbackHTML.replace(/'/g, "\\'")}';">`;
        }
        return fallbackHTML;
    }
    
    // ============================================================================
    // プロフィール関連関数
    // ============================================================================
    
    /**
     * プロフィール情報を読み込み
     */
    async function loadProfile() {
        try {
            const apiGetFunc = getFunction(apiGet, apiGetFallback);
            const data = await apiGetFunc('/api/users/me/meta/');
            
            const displayNameValue = data.display_name || data.displayName || data.display_id || data.anonId || '';
            
            // 表示名
            const displayNameInput = document.getElementById(SELECTORS.DISPLAY_NAME_INPUT);
            if (displayNameInput) {
                displayNameInput.value = displayNameValue;
            }
            
            // プロフィール文
            const bioInput = document.getElementById(SELECTORS.BIO_INPUT);
            const bioCount = document.getElementById(SELECTORS.BIO_COUNT);
            if (bioInput && bioCount) {
                if (data.bio) {
                    bioInput.value = data.bio;
                    bioCount.textContent = data.bio.length;
                }
            }
            
            // ヘッダー画像
            const headerUrl = data.header_url || data.headerUrl || '';
            const headerPreview = document.getElementById(SELECTORS.HEADER_PREVIEW);
            const deleteHeaderBtn = document.getElementById(SELECTORS.DELETE_HEADER_BTN);
            if (headerPreview) {
                if (headerUrl) {
                    headerPreview.innerHTML = `<img src="${headerUrl}" alt="header">`;
                } else {
                    headerPreview.innerHTML = '<div class="no-image">NO Image</div>';
                }

                if (deleteHeaderBtn) {
                    deleteHeaderBtn.style.display = 'inline-block';
                    deleteHeaderBtn.disabled = false;
                    deleteHeaderBtn.style.opacity = '';
                }
            }
            
            // アバター画像
            const avatarUrl = data.avatar_url || data.avatarUrl || '';
            const avatarPreview = document.getElementById(SELECTORS.AVATAR_PREVIEW);
            const deleteAvatarBtn = document.getElementById(SELECTORS.DELETE_AVATAR_BTN);
            if (avatarPreview) {
                const displayName = displayNameValue || 'U';
                avatarPreview.innerHTML = createAvatarHTML(avatarUrl, displayName);
                if (deleteAvatarBtn) {
                    deleteAvatarBtn.style.display = 'block';
                    deleteAvatarBtn.disabled = false;
                    deleteAvatarBtn.style.opacity = '';
                }
            }
        } catch (error) {
            console.error('Failed to load profile:', error);
            const showMessageFunc = getFunction(showMessage, showMessageFallback);
            const messageDiv = document.getElementById(SELECTORS.MESSAGE_DIV);
            const errorMessage = handleError(error, 'プロフィール情報の読み込みに失敗しました');
            
            if (messageDiv) {
                showMessageFunc(messageDiv, errorMessage, true);
            } else {
                alert(errorMessage);
            }
        }
    }
    
    /**
     * ヘッダー画像変更ハンドラ
     */
    function handleHeaderChange(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        headerFile = file;
        const revokeFunc = getFunction(revokeFilePreview, revokeFilePreviewFallback);
        const createFunc = getFunction(createFilePreview, createFilePreviewFallback);
        
        if (headerPreviewUrl) {
            revokeFunc(headerPreviewUrl);
        }
        
        const preview = document.getElementById(SELECTORS.HEADER_PREVIEW);
        if (preview) {
            headerPreviewUrl = createFunc(file, preview, 'image');
        }
    }
    
    /**
     * アバター画像変更ハンドラ
     */
    function handleAvatarChange(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        avatarFile = file;
        const revokeFunc = getFunction(revokeFilePreview, revokeFilePreviewFallback);
        const createFunc = getFunction(createFilePreview, createFilePreviewFallback);
        
        if (avatarPreviewUrl) {
            revokeFunc(avatarPreviewUrl);
        }
        
        const preview = document.getElementById(SELECTORS.AVATAR_PREVIEW);
        if (preview) {
            avatarPreviewUrl = createFunc(file, preview, 'image');
        }
    }
    
    /**
     * プロフィールを保存
     */
    async function saveProfile() {
        const button = document.getElementById(SELECTORS.SAVE_BUTTON);
        const messageDiv = document.getElementById(SELECTORS.MESSAGE_DIV);
        const displayNameInput = document.getElementById(SELECTORS.DISPLAY_NAME_INPUT);
        const bioInput = document.getElementById(SELECTORS.BIO_INPUT);
        
        if (!button || !messageDiv || !displayNameInput || !bioInput) {
            console.error('Required elements not found');
            return;
        }
        
        const displayName = displayNameInput.value.trim();
        const bio = bioInput.value.trim();
        
        // バリデーション
        const showMessageFunc = getFunction(showMessage, showMessageFallback);
        const setLoadingStateFunc = getFunction(setLoadingState, setLoadingStateFallback);
        const hideMessageFunc = getFunction(hideMessage, hideMessageFallback);
        
        if (displayName.length < VALIDATION.DISPLAY_NAME_MIN || displayName.length > VALIDATION.DISPLAY_NAME_MAX) {
            showMessageFunc(messageDiv, `表示名は${VALIDATION.DISPLAY_NAME_MIN}〜${VALIDATION.DISPLAY_NAME_MAX}文字で入力してください`, true);
            return;
        }
        
        if (bio.length > VALIDATION.BIO_MAX) {
            showMessageFunc(messageDiv, `プロフィール文は${VALIDATION.BIO_MAX}文字までです`, true);
            return;
        }
        
        setLoadingStateFunc(button, true, '保存中…', '変更を保存してマイページへ');
        hideMessageFunc(messageDiv);
        
        try {
            const apiPatchFunc = getFunction(apiPatch, apiPatchFallback);
            
            // 画像アップロード
            if (headerFile) {
                await uploadImage('header');
            }
            
            if (avatarFile) {
                await uploadImage('avatar');
            }
            
            // プロフィール更新
            console.log('Updating profile...', { displayName, bio });
            await apiPatchFunc('/api/user/profile/', {
                displayName: displayName,
                bio: bio
            });
            
            // プロフィール情報を再読み込み（画像の更新を反映）
            await loadProfile();
            
            showMessageFunc(messageDiv, '保存しました。マイページへ移動します…', false);
            
            setTimeout(() => {
                const setForceReloadFlagFunc = getFunction(setForceReloadFlag, (page) => {
                    localStorage.setItem(`toybox_${page}_force_reload`, '1');
                });
                setForceReloadFlagFunc('me');
                window.location.href = '/me/';
            }, 1000);
        } catch (error) {
            console.error('Profile save error:', error);
            const errorMessage = handleError(error, '保存に失敗しました');
            showMessageFunc(messageDiv, errorMessage, true);
            setLoadingStateFunc(button, false, '保存中…', '変更を保存してマイページへ');
        }
    }
    
    /**
     * ヘッダー画像をデフォルトに戻す
     */
    async function deleteHeader() {
        if (!confirm('ヘッダー画像をデフォルトに戻しますか？')) {
            return;
        }
        
        try {
            const apiPostFunc = getFunction(apiPost, apiPostFallback);
            const showMessageFunc = getFunction(showMessage, showMessageFallback);
            const result = await apiPostFunc('/api/user/profile/reset/?type=header', {});
            
            const messageDiv = document.getElementById(SELECTORS.MESSAGE_DIV);
            if (messageDiv) {
                showMessageFunc(messageDiv, result.message || 'ヘッダー画像をデフォルトに戻しました', false);
            }
            
            await loadProfile();
        } catch (error) {
            const errorMessage = handleError(error, 'ヘッダー画像のリセットに失敗しました');
            alert(errorMessage);
        }
    }
    
    /**
     * アバター画像をデフォルトに戻す
     */
    async function deleteAvatar() {
        if (!confirm('アバター画像をデフォルトに戻しますか？')) {
            return;
        }
        
        try {
            const apiPostFunc = getFunction(apiPost, apiPostFallback);
            const showMessageFunc = getFunction(showMessage, showMessageFallback);
            const result = await apiPostFunc('/api/user/profile/reset/?type=avatar', {});
            
            const messageDiv = document.getElementById(SELECTORS.MESSAGE_DIV);
            if (messageDiv) {
                showMessageFunc(messageDiv, result.message || 'アバター画像をデフォルトに戻しました', false);
            }
            
            await loadProfile();
        } catch (error) {
            const errorMessage = handleError(error, 'アバター画像のリセットに失敗しました');
            alert(errorMessage);
        }
    }
    
    // ============================================================================
    // 初期化
    // ============================================================================
    
    /**
     * プロフィールページを初期化
     */
    function initializeProfile() {
        loadProfile();
        
        // プロフィール文の文字数カウント
        const bioInput = document.getElementById(SELECTORS.BIO_INPUT);
        const bioCount = document.getElementById(SELECTORS.BIO_COUNT);
        if (bioInput && bioCount) {
            const setupCharCounterFunc = getFunction(setupCharCounter, setupCharCounterFallback);
            setupCharCounterFunc(bioInput, bioCount, VALIDATION.BIO_MAX);
        }
        
        // URL検証を設定
        const setupURLValidationFunc = getFunction(setupURLValidation, setupURLValidationFallback);
        const displayNameInput = document.getElementById(SELECTORS.DISPLAY_NAME_INPUT);
        
        if (displayNameInput) {
            setupURLValidationFunc(displayNameInput);
        }
        if (bioInput) {
            setupURLValidationFunc(bioInput);
        }
        
        // イベントリスナーの設定
        const headerInput = document.getElementById(SELECTORS.HEADER_INPUT);
        const avatarInput = document.getElementById(SELECTORS.AVATAR_INPUT);
        const saveButton = document.getElementById(SELECTORS.SAVE_BUTTON);
        const deleteHeaderBtn = document.getElementById(SELECTORS.DELETE_HEADER_BTN);
        const deleteAvatarBtn = document.getElementById(SELECTORS.DELETE_AVATAR_BTN);
        
        if (headerInput) {
            headerInput.addEventListener('change', handleHeaderChange);
        }
        if (avatarInput) {
            avatarInput.addEventListener('change', handleAvatarChange);
        }
        if (saveButton) {
            saveButton.addEventListener('click', saveProfile);
        }
        if (deleteHeaderBtn) {
            deleteHeaderBtn.addEventListener('click', deleteHeader);
        }
        if (deleteAvatarBtn) {
            deleteAvatarBtn.addEventListener('click', deleteAvatar);
        }
    }
    
    /**
     * 認証チェック（auth.jsが読み込まれていない場合のフォールバック）
     */
    function requireAuthFallback() {
        const token = getAuthToken();
        if (!token) {
            window.location.href = '/login/';
            return false;
        }
        return true;
    }
    
    /**
     * ページ読み込み時の初期化
     */
    document.addEventListener('DOMContentLoaded', function() {
        const requireAuthFunc = getFunction(requireAuth, requireAuthFallback);
        if (!requireAuthFunc()) {
            return;
        }
        
        const token = getAuthToken();
        if (!token) {
            window.location.href = '/login/';
            return;
        }
        
        const apiGetFunc = getFunction(apiGet, apiGetFallback);
        apiGetFunc('/api/users/me/')
                .then(userData => {
                    if (userData.role === 'FREE_USER') {
                        window.location.href = '/upgrade/';
                        return;
                    }
                    initializeProfile();
                })
                .catch(err => {
                    console.error('Error fetching user data:', err);
                    initializeProfile();
                });
    });
    
    // ============================================================================
    // グローバルスコープに公開（HTMLのonclick属性用）
    // ============================================================================
    window.handleHeaderChange = handleHeaderChange;
    window.handleAvatarChange = handleAvatarChange;
    window.saveProfile = saveProfile;
    window.deleteHeader = deleteHeader;
    window.deleteAvatar = deleteAvatar;
})();
