/**
 * TOYBOX オンボーディング機能
 * 初回起動時のみ表示されるコーチマーク（吹き出し）機能
 * アカウント単位で管理される（サーバー側で状態を保持）
 */

// オンボーディングステップ定義
const ONBOARDING_STEPS = [
    {
        id: 'profile-entry',
        text: 'まずはここからプロフィールを設定しよう！\n名前やアイコンを登録すると、みんなに覚えてもらいやすくなります。',
        placement: 'bottom', // top, bottom, left, right
        page: '/me/' // マイページでのみ表示
    },
    {
        id: 'media-upload-entry',
        text: 'ここから画像や動画をアップロードできます。\nAIで生成した作品を、どんどん投稿してみましょう！',
        placement: 'top',
        page: '/me/'
    },
    {
        id: 'random-prompt-entry',
        text: 'ネタに迷ったらここ！\nランダムなお題を表示して、今日の作品テーマを決めてみましょう。',
        placement: 'bottom',
        page: '/me/'
    },
    {
        id: 'game-upload-entry',
        text: '自作ゲームはここからアップロードできます。\nタイトルや説明文を添えて、TOYBOXのみんなに遊んでもらいましょう。',
        placement: 'top',
        page: '/me/'
    },
    {
        id: 'collection-cards-entry',
        text: 'あなたのカードのコレクションがここに表示されます。\nキャラクターと効果があります',
        placement: 'top',
        page: '/collection/'
    },
    {
        id: 'profile-total-likes-entry',
        text: '獲得したいいねの合計がここに表示されます、提出一覧です。',
        placement: 'bottom',
        page: '/profile/view/'
    },
    {
        id: 'sort-by-posted-entry',
        text: '最新の投稿はここからチェックできます。\n『投稿順』で並べ替えて、今アップされた作品を追いかけてみましょう。',
        placement: 'bottom',
        page: '/feed/'
    },
    {
        id: 'feed-main-entry',
        text: 'ここにみんなの投稿が並びます。\n気になる作品をクリックして、詳細を見てみましょう。',
        placement: 'top',
        page: '/feed/'
    },
    {
        id: 'like-button-entry',
        text: '気に入った作品には「いいね」を押しましょう。\nクリエイターのモチベーションアップにもつながります。',
        placement: 'top',
        page: '/feed/'
    }
];

/**
 * オンボーディング管理クラス
 */
class OnboardingManager {
    constructor() {
        this.currentStepIndex = 0;
        this.steps = ONBOARDING_STEPS;
        this.isActive = false;
        this.overlay = null;
        this.tooltip = null;
        this.targetElement = null;
    }

    /**
     * 現在のページのキーを取得
     * @returns {string} ページキー ('me', 'collection', 'profile', 'feed')
     */
    getCurrentPageKey() {
        const currentPath = window.location.pathname;
        if (currentPath.startsWith('/me/')) {
            return 'me';
        } else if (currentPath.startsWith('/collection/')) {
            return 'collection';
        } else if (currentPath.startsWith('/profile/')) {
            return 'profile';
        } else if (currentPath.startsWith('/feed/')) {
            return 'feed';
        }
        return null;
    }

    /**
     * オンボーディングが完了しているかチェック（APIから取得）
     * @returns {Promise<boolean>} 完了状態
     */
    async isCompleted() {
        // 認証されていない場合は完了とみなす（オンボーディングを表示しない）
        if (typeof getAccessToken === 'undefined' || !getAccessToken()) {
            return true;
        }

        const pageKey = this.getCurrentPageKey();
        if (!pageKey) {
            // ページキーが取得できない場合は完了とみなす
            return true;
        }

        try {
            const token = getAccessToken();
            const response = await fetch('/api/users/me/meta/', {
                headers: {
                    'Authorization': `Bearer ${token}`,
                }
            });

            if (!response.ok) {
                console.error('Failed to fetch onboarding status:', response.status);
                // APIエラーの場合は、既に完了しているとみなして表示しない（重複表示を防ぐ）
                return true;
            }

            const data = await response.json();
            // onboarding_completedがJSONオブジェクトの場合
            const completedStatus = data.onboarding_completed || {};
            const completed = completedStatus[pageKey] === true;
            console.log(`Onboarding completed status for ${pageKey}:`, completed);
            return completed;
        } catch (e) {
            console.error('Failed to check onboarding status:', e);
            // エラーの場合は、既に完了しているとみなして表示しない（重複表示を防ぐ）
            return true;
        }
    }

    /**
     * オンボーディングを完了としてマーク（APIに保存）
     */
    async markCompleted() {
        // 認証されていない場合は何もしない
        if (typeof getAccessToken === 'undefined' || !getAccessToken()) {
            return;
        }

        const pageKey = this.getCurrentPageKey();
        if (!pageKey) {
            console.log('No page key found, skipping mark completed');
            return;
        }

        try {
            const token = getAccessToken();
            
            // 現在の完了状態を取得
            const statusResponse = await fetch('/api/users/me/meta/', {
                headers: {
                    'Authorization': `Bearer ${token}`,
                }
            });
            
            let currentStatus = {};
            if (statusResponse.ok) {
                const statusData = await statusResponse.json();
                currentStatus = statusData.onboarding_completed || {};
            }
            
            // 現在のページを完了としてマーク
            currentStatus[pageKey] = true;
            
            // Use update_meta action endpoint for PATCH requests
            const response = await fetch('/api/users/me/meta/update_meta/', {
                method: 'PATCH',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    onboarding_completed: currentStatus
                })
            });

            if (!response.ok) {
                console.error('Failed to mark onboarding as completed:', response.status);
                const errorText = await response.text();
                console.error('Error response:', errorText);
            } else {
                console.log(`Onboarding marked as completed for ${pageKey} successfully`);
            }
        } catch (e) {
            console.error('Failed to mark onboarding as completed:', e);
        }
    }

    /**
     * オンボーディングをリセット（再表示用）
     */
    async reset() {
        // 認証されていない場合は何もしない
        if (typeof getAccessToken === 'undefined' || !getAccessToken()) {
            return;
        }

        const pageKey = this.getCurrentPageKey();
        if (!pageKey) {
            console.log('No page key found, skipping reset');
            return;
        }

        // アクティブ状態をリセット
        this.isActive = false;
        this.cleanup();

        try {
            const token = getAccessToken();
            
            // 現在の完了状態を取得
            const statusResponse = await fetch('/api/users/me/meta/', {
                headers: {
                    'Authorization': `Bearer ${token}`,
                }
            });
            
            let currentStatus = {};
            if (statusResponse.ok) {
                const statusData = await statusResponse.json();
                currentStatus = statusData.onboarding_completed || {};
            }
            
            // 現在のページを未完了としてマーク
            currentStatus[pageKey] = false;
            
            // Use update_meta action endpoint for PATCH requests
            const response = await fetch('/api/users/me/meta/update_meta/', {
                method: 'PATCH',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    onboarding_completed: currentStatus
                })
            });

            if (!response.ok) {
                console.error('Failed to reset onboarding:', response.status);
            } else {
                console.log(`Onboarding reset for ${pageKey} successfully`);
            }
        } catch (e) {
            console.error('Failed to reset onboarding:', e);
        }
    }

    /**
     * 現在のページで表示すべきステップを取得
     */
    getStepsForCurrentPage() {
        const currentPath = window.location.pathname;
        return this.steps.filter(step => {
            if (step.page === 'all') return true;
            return currentPath === step.page || currentPath.startsWith(step.page);
        });
    }

    /**
     * オンボーディングを開始
     */
    async start() {
        // 既にアクティブな場合は開始しない（重複実行を防ぐ）
        if (this.isActive) {
            console.log('Onboarding already active, skipping start');
            return;
        }

        // 認証されていない場合はオンボーディングを表示しない
        if (typeof getAccessToken === 'undefined' || !getAccessToken()) {
            console.log('No access token, skipping onboarding');
            return;
        }

        // APIから完了状態を取得
        const completed = await this.isCompleted();
        if (completed) {
            console.log('Onboarding already completed, skipping');
            return;
        }

        console.log('Starting onboarding...');
        const stepsForPage = this.getStepsForCurrentPage();
        if (stepsForPage.length === 0) {
            console.log('No steps for current page, skipping');
            return;
        }

        console.log(`Found ${stepsForPage.length} steps for current page`);

        // ページ読み込み完了を待つ（認証状態の更新も待つ）
        const startOnboarding = async () => {
            // 認証状態の更新を待つため、少し長めに待機
            setTimeout(async () => {
                // 再度完了状態をチェック（ページ遷移中に完了した可能性がある）
                const stillCompleted = await this.isCompleted();
                if (stillCompleted) {
                    console.log('Onboarding was completed during wait, skipping');
                    return;
                }
                await this.showStep(0, stepsForPage);
            }, 1500);
        };

        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', startOnboarding);
        } else {
            startOnboarding();
        }
    }

    /**
     * ステップを表示
     */
    async showStep(stepIndex, steps) {
        // 完了状態を再チェック（ページ遷移中に完了した可能性がある）
        const completed = await this.isCompleted();
        if (completed) {
            console.log('Onboarding was completed, stopping step display');
            this.cleanup();
            this.isActive = false;
            return;
        }

        if (stepIndex >= steps.length) {
            await this.complete();
            return;
        }

        const step = steps[stepIndex];
        const element = document.getElementById(step.id);

        if (!element) {
            // 要素が見つからない場合は次のステップへ（最大3回リトライ）
            const retryCount = step.retryCount || 0;
            if (retryCount < 3) {
                step.retryCount = retryCount + 1;
                console.warn(`Onboarding target element not found: ${step.id}, retrying... (${retryCount + 1}/3)`);
                setTimeout(async () => await this.showStep(stepIndex, steps), 500);
                return;
            }
            console.warn(`Onboarding target element not found: ${step.id}, skipping`);
            await this.showStep(stepIndex + 1, steps);
            return;
        }

        // 要素が表示されているかチェック
        const rect = element.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0) {
            // 要素が非表示の場合は次のステップへ（最大3回リトライ）
            const retryCount = step.retryCount || 0;
            if (retryCount < 3) {
                step.retryCount = retryCount + 1;
                console.warn(`Onboarding target element is not visible: ${step.id}, retrying... (${retryCount + 1}/3)`);
                setTimeout(async () => await this.showStep(stepIndex, steps), 500);
                return;
            }
            console.warn(`Onboarding target element is not visible: ${step.id}, skipping`);
            await this.showStep(stepIndex + 1, steps);
            return;
        }
        
        // リトライカウントをリセット
        step.retryCount = 0;

        this.currentStepIndex = stepIndex;
        this.isActive = true;
        this.targetElement = element;

        // オーバーレイとツールチップを表示
        this.showOverlay();
        this.showTooltip(step, element);
    }

    /**
     * オーバーレイを表示
     */
    showOverlay() {
        if (this.overlay) {
            this.overlay.remove();
        }

        this.overlay = document.createElement('div');
        this.overlay.id = 'onboarding-overlay';
        this.overlay.className = 'onboarding-overlay';
        document.body.appendChild(this.overlay);

        // オーバーレイクリックでスキップ
        this.overlay.addEventListener('click', async (e) => {
            if (e.target === this.overlay) {
                await this.skip();
            }
        });
    }

    /**
     * ツールチップ（吹き出し）を表示
     */
    showTooltip(step, targetElement) {
        if (this.tooltip) {
            this.tooltip.remove();
        }

        const rect = targetElement.getBoundingClientRect();
        const tooltip = document.createElement('div');
        tooltip.id = 'onboarding-tooltip';
        tooltip.className = 'onboarding-tooltip';
        tooltip.setAttribute('role', 'dialog');
        tooltip.setAttribute('aria-label', 'オンボーディングガイド');

        // テキストを改行で分割
        const lines = step.text.split('\n');
        const textContent = lines.map(line => {
            const p = document.createElement('p');
            p.textContent = line;
            return p.outerHTML;
        }).join('');

        tooltip.innerHTML = `
            <div class="onboarding-tooltip-content">
                <div class="onboarding-tooltip-text">${textContent}</div>
                <div class="onboarding-tooltip-actions">
                    <button class="onboarding-btn onboarding-btn-primary" id="onboarding-next-btn" aria-label="次へ">
                        次へ
                    </button>
                    <button class="onboarding-btn onboarding-btn-secondary" id="onboarding-skip-btn" aria-label="スキップ">
                        スキップ
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(tooltip);
        this.tooltip = tooltip;

        // 位置を計算して配置
        this.positionTooltip(step, rect);

        // ターゲット要素をハイライト
        this.highlightTarget(targetElement, rect);

        // イベントリスナーを設定
        document.getElementById('onboarding-next-btn').addEventListener('click', async () => {
            await this.next();
        });

        document.getElementById('onboarding-skip-btn').addEventListener('click', async () => {
            await this.skip();
        });

        // キーボード操作
        tooltip.addEventListener('keydown', async (e) => {
            if (e.key === 'Escape') {
                await this.skip();
            } else if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                await this.next();
            }
        });

        // フォーカスを設定
        const nextBtn = document.getElementById('onboarding-next-btn');
        if (nextBtn) {
            nextBtn.focus();
        }
    }

    /**
     * ツールチップの位置を計算して配置
     */
    positionTooltip(step, targetRect) {
        const tooltipRect = this.tooltip.getBoundingClientRect();
        const padding = 16;
        let top = 0;
        let left = 0;

        switch (step.placement) {
            case 'top':
                top = targetRect.top - tooltipRect.height - padding;
                left = targetRect.left + (targetRect.width / 2) - (tooltipRect.width / 2);
                break;
            case 'bottom':
                top = targetRect.bottom + padding;
                left = targetRect.left + (targetRect.width / 2) - (tooltipRect.width / 2);
                break;
            case 'left':
                top = targetRect.top + (targetRect.height / 2) - (tooltipRect.height / 2);
                left = targetRect.left - tooltipRect.width - padding;
                break;
            case 'right':
                top = targetRect.top + (targetRect.height / 2) - (tooltipRect.height / 2);
                left = targetRect.right + padding;
                break;
        }

        // 画面外に出ないように調整
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;

        if (left < padding) {
            left = padding;
        } else if (left + tooltipRect.width > viewportWidth - padding) {
            left = viewportWidth - tooltipRect.width - padding;
        }

        if (top < padding) {
            top = padding;
        } else if (top + tooltipRect.height > viewportHeight - padding) {
            top = viewportHeight - tooltipRect.height - padding;
        }

        this.tooltip.style.top = `${top + window.scrollY}px`;
        this.tooltip.style.left = `${left + window.scrollX}px`;
    }

    /**
     * ターゲット要素をハイライト
     */
    highlightTarget(element, rect) {
        // 既存のハイライトを削除
        const existingHighlight = document.getElementById('onboarding-highlight');
        if (existingHighlight) {
            existingHighlight.remove();
        }

        const highlight = document.createElement('div');
        highlight.id = 'onboarding-highlight';
        highlight.className = 'onboarding-highlight';
        highlight.style.position = 'fixed';
        highlight.style.top = `${rect.top + window.scrollY}px`;
        highlight.style.left = `${rect.left + window.scrollX}px`;
        highlight.style.width = `${rect.width}px`;
        highlight.style.height = `${rect.height}px`;
        highlight.style.pointerEvents = 'none';
        highlight.style.zIndex = '10001';
        highlight.style.borderRadius = '8px';
        highlight.style.boxShadow = `0 0 0 9999px rgba(0, 0, 0, 0.7), 0 0 0 4px var(--steam-gold-400)`;
        highlight.style.transition = 'all 0.3s ease';

        document.body.appendChild(highlight);

        // スクロール時に位置を更新
        const updateHighlight = () => {
            if (element && document.body.contains(element)) {
                const newRect = element.getBoundingClientRect();
                highlight.style.top = `${newRect.top + window.scrollY}px`;
                highlight.style.left = `${newRect.left + window.scrollX}px`;
                highlight.style.width = `${newRect.width}px`;
                highlight.style.height = `${newRect.height}px`;
            }
        };

        window.addEventListener('scroll', updateHighlight, { passive: true });
        window.addEventListener('resize', updateHighlight, { passive: true });

        // クリーンアップ用の参照を保存
        this.highlightCleanup = () => {
            window.removeEventListener('scroll', updateHighlight);
            window.removeEventListener('resize', updateHighlight);
        };
    }

    /**
     * 次のステップへ
     */
    async next() {
        const stepsForPage = this.getStepsForCurrentPage();
        this.cleanup();
        await this.showStep(this.currentStepIndex + 1, stepsForPage);
    }

    /**
     * スキップ（オンボーディングを終了）
     */
    async skip() {
        await this.complete();
    }

    /**
     * オンボーディングを完了
     */
    async complete() {
        console.log('Completing onboarding...');
        this.cleanup();
        await this.markCompleted();
        this.isActive = false;
        console.log('Onboarding completed');
    }

    /**
     * クリーンアップ
     */
    cleanup() {
        if (this.overlay) {
            this.overlay.remove();
            this.overlay = null;
        }

        if (this.tooltip) {
            this.tooltip.remove();
            this.tooltip = null;
        }

        const highlight = document.getElementById('onboarding-highlight');
        if (highlight) {
            highlight.remove();
        }

        if (this.highlightCleanup) {
            this.highlightCleanup();
            this.highlightCleanup = null;
        }

        this.targetElement = null;
    }
}

// グローバルインスタンス
let onboardingManager = null;

/**
 * オンボーディングを初期化
 */
async function initOnboarding() {
    if (!onboardingManager) {
        onboardingManager = new OnboardingManager();
    }
    await onboardingManager.start();
}

/**
 * オンボーディングをリセット（再表示用）
 */
async function resetOnboarding() {
    if (!onboardingManager) {
        onboardingManager = new OnboardingManager();
    }
    await onboardingManager.reset();
    await onboardingManager.start();
}

// グローバルに公開（設定画面などから呼び出し可能）
window.initOnboarding = initOnboarding;
window.resetOnboarding = resetOnboarding;

// base.htmlの認証処理の後に呼び出されるため、ここでは自動開始しない

