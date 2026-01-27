# TOYBOXシステム構成図 (Mermaid)

## システム全体構成図

```mermaid
graph TB
    subgraph Internet["🌐 インターネット"]
        User["👤 ユーザー<br/>(ブラウザ)"]
        StudySphere["🔐 StudySphere<br/>(外部SSO)"]
    end
    
    subgraph Server["🖥️ ConoHa VPS (160.251.168.144)"]
        subgraph Caddy["Caddyサーバー"]
            CaddyWeb["🌐 Caddy<br/>リバースプロキシ<br/>SSL/TLS<br/>:80/:443"]
        end
        
        subgraph BackendNetwork["backend_default ネットワーク"]
            subgraph Django["Djangoアプリケーション"]
                Web["🐍 Django<br/>(Gunicorn)<br/>:8000"]
            end
            
            subgraph Database["データベース"]
                PostgreSQL["📦 PostgreSQL<br/>:5432"]
            end
            
            subgraph Cache["キャッシュ/メッセージング"]
                Redis["🔴 Redis<br/>:6379"]
            end
            
            subgraph Tasks["非同期処理"]
                Worker["⚙️ Celery Worker"]
                Beat["⏰ Celery Beat<br/>(スケジューラ)"]
            end
        end
        
        subgraph Volumes["📁 Dockerボリューム"]
            StaticVol["静的ファイル<br/>(backend_static_volume)"]
            MediaVol["メディアファイル<br/>(media_volume)"]
            DBVol["DBデータ<br/>(postgres_data)"]
        end
    end
    
    User -->|HTTPS| CaddyWeb
    CaddyWeb -->|/api/*| Web
    CaddyWeb -->|/static/*| StaticVol
    CaddyWeb -.->|reverse_proxy| Web
    
    Web --> PostgreSQL
    Web --> Redis
    Worker --> Redis
    Worker --> PostgreSQL
    Beat --> Redis
    
    Web --> MediaVol
    Web --> StaticVol
    PostgreSQL --> DBVol
    
    User -.->|SSO認証| StudySphere
    StudySphere -.->|チケット発行| Web
    
    style User fill:#e3f2fd
    style StudySphere fill:#fff3e0
    style CaddyWeb fill:#c8e6c9
    style Web fill:#bbdefb
    style PostgreSQL fill:#f8bbd0
    style Redis fill:#ffccbc
    style Worker fill:#d1c4e9
    style Beat fill:#d1c4e9
```

---

## コンテナ構成図

```mermaid
graph LR
    subgraph Production["本番環境コンテナ"]
        Caddy["toybox-caddy<br/>Caddy 2<br/>:80/:443"]
    end
    
    subgraph Backend["バックエンドコンテナ群"]
        Web["backend-web-1<br/>Django+Gunicorn<br/>:8000"]
        DB["backend-db-1<br/>PostgreSQL 15<br/>:5432"]
        Redis["backend-redis-1<br/>Redis 7<br/>:6379"]
        Worker["backend-worker-1<br/>Celery Worker"]
        Beat["backend-beat-1<br/>Celery Beat"]
    end
    
    Caddy -->|HTTP| Web
    Web --> DB
    Web --> Redis
    Worker --> DB
    Worker --> Redis
    Beat --> Redis
    
    style Caddy fill:#4caf50,color:#fff
    style Web fill:#2196f3,color:#fff
    style DB fill:#e91e63,color:#fff
    style Redis fill:#ff5722,color:#fff
    style Worker fill:#9c27b0,color:#fff
    style Beat fill:#9c27b0,color:#fff
```

---

## リクエストフロー図

```mermaid
sequenceDiagram
    participant U as 👤 ユーザー
    participant C as 🌐 Caddy
    participant D as 🐍 Django
    participant P as 📦 PostgreSQL
    participant R as 🔴 Redis
    
    Note over U,R: Webページリクエスト
    U->>C: HTTPS GET /me/
    C->>D: reverse_proxy :8000
    D->>R: キャッシュチェック
    R-->>D: キャッシュミス
    D->>P: SELECT user data
    P-->>D: User data
    D->>R: キャッシュ保存
    D-->>C: HTML Response
    C-->>U: HTTPS Response
    
    Note over U,R: 静的ファイルリクエスト
    U->>C: HTTPS GET /static/css/base.css
    C-->>U: File (直接配信)
    
    Note over U,R: APIリクエスト
    U->>C: HTTPS GET /api/users/me/meta/<br/>Authorization: Bearer [token]
    C->>D: reverse_proxy :8000
    D->>D: JWT検証
    D->>P: SELECT user_meta
    P-->>D: Meta data
    D-->>C: JSON Response
    C-->>U: HTTPS Response
```

---

## StudySphere SSO認証フロー

```mermaid
sequenceDiagram
    participant U as 👤 ユーザー
    participant SS as 🔐 StudySphere
    participant T as 🌐 TOYBOX
    participant D as 🐍 Django
    participant P as 📦 PostgreSQL
    
    U->>SS: ログイン
    SS-->>U: ログイン成功
    U->>SS: TOYBOXボタンをクリック
    SS->>SS: チケット生成
    SS->>U: リダイレクト<br/>toybox.ayatori-inc.co.jp/sso/login/?ticket=XXX
    U->>T: HTTPS GET /sso/login/?ticket=XXX
    T->>D: チケット検証リクエスト
    D->>SS: POST /api/sso/verify<br/>ticket=XXX
    SS-->>D: ユーザー情報<br/>{user_id, login_code, ...}
    D->>P: ユーザー検索/作成
    P-->>D: User record
    D->>D: JWT生成
    D-->>T: JWT tokens
    T-->>U: リダイレクト /me/<br/>Set tokens in localStorage
    U->>T: マイページ表示
```

---

## データモデル概要

```mermaid
erDiagram
    USER ||--o{ USER_META : has
    USER ||--o{ SUBMISSION : creates
    USER ||--o{ USER_CARD : owns
    USER ||--o{ USER_TITLE : has
    SUBMISSION ||--o{ LIKE : receives
    SUBMISSION ||--o{ COMMENT : receives
    CARD ||--o{ USER_CARD : "awarded to"
    TITLE ||--o{ USER_TITLE : "awarded to"
    
    USER {
        int id PK
        string email
        string display_id UK
        string password_hash
        boolean is_superuser
        int studysphere_user_id
        string studysphere_login_code
    }
    
    USER_META {
        int id PK
        int user_id FK
        string display_name
        text bio
        string avatar_url
        string header_url
        int active_title_id FK
    }
    
    SUBMISSION {
        int id PK
        int user_id FK
        string type
        string image_url
        string video_url
        string game_url
        text caption
        array hashtags
        int likes_count
    }
    
    CARD {
        int id PK
        string code UK
        string name
        string rarity
        string image_url
    }
    
    TITLE {
        int id PK
        string name UK
        string color
        int duration_days
        string image_url
    }
```

---

## デプロイメント構成

```mermaid
graph TB
    subgraph Local["💻 開発環境 (ローカル)"]
        LocalCode["ソースコード<br/>c:\github\toybox"]
    end
    
    subgraph Transfer["📤 デプロイ"]
        WinSCP["WinSCP<br/>(ファイル転送)"]
    end
    
    subgraph Production["🖥️ 本番環境 (ConoHa VPS)"]
        ServerCode["ソースコード<br/>/var/www/toybox"]
        
        subgraph DockerCompose["Docker Compose"]
            BackendCompose["docker-compose.yml<br/>(backend)"]
            ProdCompose["docker-compose.prod.yml<br/>(caddy)"]
        end
        
        BackendCompose --> Containers1["バックエンドコンテナ群"]
        ProdCompose --> Containers2["Caddyコンテナ"]
    end
    
    LocalCode -->|WinSCP| WinSCP
    WinSCP -->|SSH/SFTP| ServerCode
    ServerCode -->|docker compose up| DockerCompose
    
    style LocalCode fill:#e3f2fd
    style WinSCP fill:#fff3e0
    style ServerCode fill:#c8e6c9
    style Containers1 fill:#bbdefb
    style Containers2 fill:#bbdefb
```

---

**作成日**: 2026年1月23日  
**TOYBOX開発チーム**

## 使用方法

このMermaid記法は以下のツールで図として表示できます：

1. **GitHub/GitLab**: README.mdにそのまま貼り付け
2. **Mermaid Live Editor**: https://mermaid.live/
3. **VS Code**: Mermaid拡張機能をインストール
4. **Notion**: `/code` でMermaidブロックを作成
5. **Confluence**: Mermaid for Confluenceプラグイン
