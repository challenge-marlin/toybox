// スプラッシュスクリーンの処理
document.addEventListener('DOMContentLoaded', function() {
    const splash = document.getElementById('splash-screen');
    if (splash) {
        setTimeout(() => {
            splash.classList.add('fade');
        }, 1200);
        setTimeout(() => {
            splash.style.display = 'none';
        }, 1700);
    }

    // スムーススクロール
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // スクロール時のアニメーション
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // アニメーション対象の要素を監視
    document.querySelectorAll('.feature-card, .step, .card-game-content, .target-card, .pricing-card').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });

    // 問い合わせフォームの処理は削除（外部リンクに変更）
    const contactForm = document.getElementById('contact-form');
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            // 基本的なバリデーション（サーバー側でも検証されます）
            const name = document.getElementById('name').value.trim();
            const email = document.getElementById('email').value.trim();
            const type = document.getElementById('type').value;
            const plan = document.getElementById('plan').value;
            
            if (!name || !email || !type || !plan) {
                e.preventDefault();
                alert('必須項目をすべて入力してください。');
                return false;
            }
            
            // メールアドレスの形式チェック
            const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailPattern.test(email)) {
                e.preventDefault();
                alert('有効なメールアドレスを入力してください。');
                return false;
            }
            
            // フォーム送信を許可（PHP側で処理）
            return true;
        });
    }
});
