/**
 * API呼び出しヘルパー
 * 統一されたfetchラッパーとエラーハンドリング
 */

/**
 * 認証トークンを取得
 */
function getAccessToken() {
    return localStorage.getItem('access_token') || '';
}

/**
 * CSRFトークンを取得
 */
function getCsrfToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    return token ? token.value : '';
}

/**
 * 統一されたAPI呼び出し関数
 * @param {string} url - APIエンドポイント
 * @param {object} options - fetchオプション
 * @returns {Promise<Response>}
 */
async function apiCall(url, options = {}) {
    const token = getAccessToken();
    const csrftoken = getCsrfToken();
    
    const defaultHeaders = {
        'Content-Type': 'application/json',
    };
    
    // 認証トークンがある場合は追加
    if (token) {
        defaultHeaders['Authorization'] = `Bearer ${token}`;
    }
    
    // CSRFトークンがある場合は追加
    if (csrftoken) {
        defaultHeaders['X-CSRFToken'] = csrftoken;
    }
    
    // カスタムヘッダーで上書き
    const headers = {
        ...defaultHeaders,
        ...(options.headers || {})
    };
    
    // FormDataの場合はContent-Typeを削除（ブラウザが自動設定）
    if (options.body instanceof FormData) {
        delete headers['Content-Type'];
    }
    
    try {
        const response = await fetch(url, {
            ...options,
            headers
        });
        
        // 401エラーの場合は認証エラーとして処理
        if (response.status === 401) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/login/';
            throw new Error('認証が必要です');
        }
        
        return response;
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}

/**
 * GETリクエスト
 * @param {string} url - APIエンドポイント
 * @param {object} params - クエリパラメータ
 * @returns {Promise<object>}
 */
async function apiGet(url, params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const fullUrl = queryString ? `${url}?${queryString}` : url;
    
    const response = await apiCall(fullUrl, {
        method: 'GET'
    });
    
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
    }
    
    return await response.json();
}

/**
 * POSTリクエスト
 * @param {string} url - APIエンドポイント
 * @param {object|FormData} data - リクエストボディ
 * @returns {Promise<object>}
 */
async function apiPost(url, data) {
    const isFormData = data instanceof FormData;
    const body = isFormData ? data : JSON.stringify(data);
    
    const response = await apiCall(url, {
        method: 'POST',
        body
    });
    
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
    }
    
    return await response.json();
}

/**
 * PATCHリクエスト
 * @param {string} url - APIエンドポイント
 * @param {object|FormData} data - リクエストボディ
 * @returns {Promise<object>}
 */
async function apiPatch(url, data) {
    const isFormData = data instanceof FormData;
    const body = isFormData ? data : JSON.stringify(data);
    
    const response = await apiCall(url, {
        method: 'PATCH',
        body
    });
    
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
    }
    
    return await response.json();
}

/**
 * DELETEリクエスト
 * @param {string} url - APIエンドポイント
 * @returns {Promise<object>}
 */
async function apiDelete(url) {
    const response = await apiCall(url, {
        method: 'DELETE'
    });
    
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
    }
    
    // DELETEリクエストは空のレスポンスの場合がある
    const text = await response.text();
    return text ? JSON.parse(text) : {};
}





