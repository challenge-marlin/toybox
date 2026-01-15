/**
 * Penalty / moderation message display.
 *
 * Goal:
 * - Show WARNING / SUSPEND / BAN messages even when the user stays logged in.
 * - Trigger on page access (DOMContentLoaded) and optionally periodic re-check.
 *
 * Data source:
 * - GET /api/users/me/ (UserSerializer.penalty)
 */

function _toyboxPenaltyHash(penalty) {
    if (!penalty || !penalty.type || !penalty.message) return '';
    return `${penalty.type}:${penalty.message}`;
}

function _toyboxShowMiniToast(text) {
    const existing = document.getElementById('toybox-penalty-toast');
    if (existing) existing.remove();

    const el = document.createElement('div');
    el.id = 'toybox-penalty-toast';
    el.style.cssText = [
        'position: fixed',
        'right: 16px',
        'top: 16px',
        'z-index: 20060',
        'background: rgba(0,0,0,0.85)',
        'color: white',
        'border: 1px solid rgba(255,255,255,0.15)',
        'border-radius: 10px',
        'padding: 10px 12px',
        'font-size: 12px',
        'max-width: 360px',
        'box-shadow: 0 10px 15px -3px rgba(0,0,0,0.35)',
    ].join(';');
    el.textContent = text;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 4000);
}

async function _toyboxAckWarningPenalty() {
    try {
        const token = typeof getAccessToken === 'function' ? getAccessToken() : null;
        if (!token) return;
        await fetch('/api/users/penalty/ack/', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({}),
        });
    } catch (e) {
        // ignore
    }
}

function _toyboxShowPenaltyModal(penalty) {
    // Remove existing modal if any
    const existing = document.getElementById('toybox-penalty-modal');
    if (existing) existing.remove();

    const overlay = document.createElement('div');
    overlay.id = 'toybox-penalty-modal';
    overlay.style.cssText = [
        'position: fixed',
        'inset: 0',
        'background: rgba(0,0,0,0.6)',
        'z-index: 20050',
        'display: flex',
        'align-items: center',
        'justify-content: center',
        'padding: 16px',
    ].join(';');

    const card = document.createElement('div');
    card.style.cssText = [
        'max-width: 560px',
        'width: 100%',
        'background: var(--steam-iron-900)',
        'border: 1px solid var(--steam-iron-700)',
        'border-radius: 10px',
        'box-shadow: 0 20px 25px -5px rgba(0,0,0,0.35)',
        'padding: 16px',
        'color: var(--steam-iron-100)',
    ].join(';');

    const title = document.createElement('div');
    title.style.cssText = 'font-weight: 700; font-size: 16px; margin-bottom: 8px; color: var(--steam-gold-300);';
    const type = (penalty.type || '').toUpperCase();
    title.textContent =
        type === 'BAN' ? 'アカウントにBAN処置が適用されています' :
        type === 'SUSPEND' ? 'アカウント停止処置が適用されています' :
        '運営からの警告があります';

    const body = document.createElement('div');
    body.style.cssText = [
        'white-space: pre-wrap',
        'line-height: 1.6',
        'font-size: 14px',
        'color: var(--steam-iron-200)',
        'margin-bottom: 12px',
        'border: 1px solid var(--steam-iron-800)',
        'background: rgba(255,255,255,0.03)',
        'border-radius: 8px',
        'padding: 12px',
    ].join(';');
    body.textContent = penalty.message || '';

    const actions = document.createElement('div');
    actions.style.cssText = 'display: flex; justify-content: flex-end; gap: 8px;';

    const okBtn = document.createElement('button');
    okBtn.type = 'button';
    okBtn.textContent = (type === 'BAN' || type === 'SUSPEND') ? 'ログアウトする' : 'OK';
    okBtn.style.cssText = [
        'padding: 10px 14px',
        'border-radius: 8px',
        'border: none',
        'cursor: pointer',
        'font-weight: 700',
        'background: var(--steam-gold-500)',
        'color: #000',
    ].join(';');

    okBtn.addEventListener('click', () => {
        overlay.remove();
        // For ban/suspend, force logout on acknowledgment (prevents continued use)
        if (type === 'BAN' || type === 'SUSPEND') {
            if (typeof clearAuth === 'function') clearAuth();
            window.location.href = '/login/';
            return;
        }
        // For warning, acknowledge so it won't keep popping up
        if (type === 'WARNING') {
            _toyboxAckWarningPenalty();
        }
    });

    actions.appendChild(okBtn);
    card.appendChild(title);
    card.appendChild(body);
    card.appendChild(actions);
    overlay.appendChild(card);
    document.body.appendChild(overlay);
}

async function initPenaltyCheck(options = {}) {
    const {
        intervalMs = 5000, // near real-time while staying on the same page
    } = options;

    if (typeof hasValidToken !== 'function' || typeof getAccessToken !== 'function') return;
    if (!hasValidToken()) return;

    const runCheck = async () => {
        try {
            const token = getAccessToken();
            if (!token) return;

            const res = await fetch('/api/users/me/', {
                headers: { 'Authorization': `Bearer ${token}` },
            });
            if (!res.ok) return;

            const data = await res.json();
            const penalty = data && data.penalty ? data.penalty : null;
            const key = `toybox_penalty_seen_${data.id || 'me'}`;
            const last = localStorage.getItem(key) || '';

            // If penalty was lifted (解除) while staying logged in, notify once.
            if ((!penalty || !penalty.type || !penalty.message) && last) {
                localStorage.setItem(key, '');
                _toyboxShowMiniToast('運営による制限が解除されました。');
                return;
            }

            if (!penalty || !penalty.type || !penalty.message) return;

            // De-dup: show only when penalty content changes.
            const hash = _toyboxPenaltyHash(penalty);
            if (hash && hash !== last) {
                localStorage.setItem(key, hash);
                _toyboxShowPenaltyModal(penalty);
            }
        } catch (e) {
            // Do not block the page if penalty check fails
            console.warn('Penalty check failed:', e);
        }
    };

    await runCheck();

    // Periodic re-check (optional)
    if (intervalMs && intervalMs > 0) {
        setInterval(runCheck, intervalMs);
    }

    // Also re-check immediately on tab focus / visibility restore.
    window.addEventListener('focus', runCheck);
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') runCheck();
    });
}


