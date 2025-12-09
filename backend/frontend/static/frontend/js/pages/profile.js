/**
 * プロフィール設定ページのJavaScript
 */

(function() {
    'use strict';
    
    let headerFile = null;
    let avatarFile = null;
    let headerPreviewUrl = null;
    let avatarPreviewUrl = null;
    
    /**
     * プロフィール情報を読み込み
     */
    async function loadProfile() {
        try {
            const data = await apiGet('/api/users/me/meta/');
            
            // 表示名
            const displayNameInput = document.getElementById('display-name-input');
            if (displayNameInput) {
                if (data.display_name) {
                    displayNameInput.value = data.display_name;
                } else if (data.display_id) {
                    displayNameInput.value = data.display_id;
                }
            }
            
            // プロフィール文
            const bioInput = document.getElementById('bio-input');
            const bioCount = document.getElementById('bio-count');
            if (bioInput && bioCount) {
                if (data.bio) {
                    bioInput.value = data.bio;
                    bioCount.textContent = data.bio.length;
                }
            }
            
            // ヘッダー画像
            const headerPreview = document.getElementById('header-preview');
            if (headerPreview && data.header_url) {
                headerPreview.innerHTML = `<img src="${data.header_url}" alt="header">`;
            }
            
            // アバター画像
            const avatarPreview = document.getElementById('avatar-preview');
            if (avatarPreview) {
                if (data.avatar_url) {
                    const displayName = data.display_name || data.display_id || 'U';
                    const firstChar = displayName.charAt(0).toUpperCase();
                    avatarPreview.innerHTML = `<img src="${data.avatar_url}" alt="avatar" onerror="this.style.display='none'; this.parentElement.innerHTML='<span style=\\'display: flex; align-items: center; justify-content: center; height: 100%; width: 100%; background: var(--steam-iron-800); color: var(--steam-gold-300); font-size: 1.5rem; font-weight: 600;\\'>${firstChar}</span>';">`;
                } else {
                    const displayName = data.display_name || data.display_id || 'U';
                    const firstChar = displayName.charAt(0).toUpperCase();
                    avatarPreview.innerHTML = `<span style="display: flex; align-items: center; justify-content: center; height: 100%; width: 100%; background: var(--steam-iron-800); color: var(--steam-gold-300); font-size: 1.5rem; font-weight: 600;">${firstChar}</span>`;
                }
            }
        } catch (error) {
            console.error('Failed to load profile:', error);
            handleApiError(error, 'プロフィール情報の読み込みに失敗しました');
        }
    }
    
    /**
     * ヘッダー画像変更ハンドラ
     */
    function handleHeaderChange(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        headerFile = file;
        if (headerPreviewUrl) {
            revokeFilePreview(headerPreviewUrl);
        }
        
        const preview = document.getElementById('header-preview');
        if (preview) {
            headerPreviewUrl = createFilePreview(file, preview, 'image');
        }
    }
    
    /**
     * アバター画像変更ハンドラ
     */
    function handleAvatarChange(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        avatarFile = file;
        if (avatarPreviewUrl) {
            revokeFilePreview(avatarPreviewUrl);
        }
        
        const preview = document.getElementById('avatar-preview');
        if (preview) {
            avatarPreviewUrl = createFilePreview(file, preview, 'image');
        }
    }
    
    /**
     * プロフィールを保存
     */
    async function saveProfile() {
        const button = document.getElementById('save-button');
        const messageDiv = document.getElementById('message');
        const displayNameInput = document.getElementById('display-name-input');
        const bioInput = document.getElementById('bio-input');
        
        if (!button || !messageDiv || !displayNameInput || !bioInput) {
            console.error('Required elements not found');
            return;
        }
        
        const displayName = displayNameInput.value.trim();
        const bio = bioInput.value.trim();
        
        // バリデーション
        if (displayName.length < 1 || displayName.length > 50) {
            showMessage(messageDiv, '表示名は1〜50文字で入力してください', true);
            return;
        }
        
        if (bio.length > 1000) {
            showMessage(messageDiv, 'プロフィール文は1000文字までです', true);
            return;
        }
        
        setLoadingState(button, true, '保存中…', '変更を保存してマイページへ');
        hideMessage(messageDiv);
        
        try {
            // 画像アップロード
            if (headerFile) {
                const formData = new FormData();
                formData.append('file', headerFile);
                await apiPost('/api/user/profile/upload?type=header', formData);
            }
            
            if (avatarFile) {
                const formData = new FormData();
                formData.append('file', avatarFile);
                await apiPost('/api/user/profile/upload?type=avatar', formData);
            }
            
            // プロフィール更新
            await apiPatch('/api/user/profile/', {
                displayName: displayName,
                bio: bio
            });
            
            showMessage(messageDiv, '保存しました。マイページへ移動します…', false);
            
            setTimeout(() => {
                setForceReloadFlag('me');
                window.location.href = '/me/';
            }, 1000);
        } catch (error) {
            const errorMessage = handleApiError(error, '保存に失敗しました');
            showMessage(messageDiv, errorMessage, true);
            setLoadingState(button, false, '保存中…', '変更を保存してマイページへ');
        }
    }
    
    /**
     * 初期化
     */
    function initializeProfile() {
        loadProfile();
        
        // プロフィール文の文字数カウント
        const bioInput = document.getElementById('bio-input');
        const bioCount = document.getElementById('bio-count');
        if (bioInput && bioCount) {
            setupCharCounter(bioInput, bioCount, 1000);
        }
        
        // イベントリスナーの設定
        const headerInput = document.getElementById('header-input');
        const avatarInput = document.getElementById('avatar-input');
        const saveButton = document.getElementById('save-button');
        
        if (headerInput) {
            headerInput.addEventListener('change', handleHeaderChange);
        }
        
        if (avatarInput) {
            avatarInput.addEventListener('change', handleAvatarChange);
        }
        
        if (saveButton) {
            saveButton.addEventListener('click', saveProfile);
        }
    }
    
    /**
     * ページ読み込み時の初期化
     */
    document.addEventListener('DOMContentLoaded', function() {
        // 認証チェック
        if (!requireAuth()) {
            return;
        }
        
        // ロールチェック：一般ユーザー（FREE_USER）はこのページにアクセスできない
        const token = getAccessToken();
        if (token) {
            apiGet('/api/users/me/')
                .then(userData => {
                    if (userData.role === 'FREE_USER') {
                        window.location.href = '/upgrade/';
                        return;
                    }
                    // 課金ユーザー以上の場合は通常の処理を続行
                    initializeProfile();
                })
                .catch(err => {
                    console.error('Error fetching user data:', err);
                    // エラーが発生した場合は通常の処理を続行
                    initializeProfile();
                });
        } else {
            // トークンがない場合はログインページにリダイレクト
            window.location.href = '/login/';
        }
    });
    
    // グローバルスコープに公開（HTMLのonchange属性用）
    window.handleHeaderChange = handleHeaderChange;
    window.handleAvatarChange = handleAvatarChange;
    window.saveProfile = saveProfile;
})();



