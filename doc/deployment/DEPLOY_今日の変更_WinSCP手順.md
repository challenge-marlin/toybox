# 今日の変更デプロイ手順（WinSCP）

ホスティングへ反映するための、WinSCPアップロード対象とサーバー上で実行するコマンドをまとめます。

---

## 1. WinSCPでアップロードするファイル

**ローカル**: `C:\github\toybox\`  
**サーバー**: `/var/www/toybox/`

以下を**同名パス**で上書きアップロードしてください。

| ローカルパス | サーバー側の配置先 |
|-------------|-------------------|
| `backend/toybox/image_utils.py` | `/var/www/toybox/backend/toybox/image_utils.py` |
| `backend/users/views.py` | `/var/www/toybox/backend/users/views.py` |
| `backend/users/serializers.py` | `/var/www/toybox/backend/users/serializers.py` |
| `backend/submissions/views.py` | `/var/www/toybox/backend/submissions/views.py` |
| `backend/submissions/serializers.py` | `/var/www/toybox/backend/submissions/serializers.py` |
| `backend/gamification/services.py` | `/var/www/toybox/backend/gamification/services.py` |
| `backend/gamification/views.py` | `/var/www/toybox/backend/gamification/views.py` |
| `backend/gamification/admin.py` | `/var/www/toybox/backend/gamification/admin.py` |
| `backend/gamification/management/commands/init_titles.py` | `/var/www/toybox/backend/gamification/management/commands/init_titles.py` |
| `backend/frontend/templates/frontend/collection.html` | `/var/www/toybox/backend/frontend/templates/frontend/collection.html` |
| `backend/frontend/templates/frontend/profile_view.html` | `/var/www/toybox/backend/frontend/templates/frontend/profile_view.html` |

**ミグレーション**（Card の attribute 等を追加した `0004`）がまだサーバーにない場合のみ、以下もアップロードします。

| ローカルパス | サーバー側の配置先 |
|-------------|-------------------|
| `backend/gamification/migrations/0004_add_card_fields_attribute_atk_def_type_buff.py` | `/var/www/toybox/backend/gamification/migrations/0004_add_card_fields_attribute_atk_def_type_buff.py` |

---

## 2. 本番環境への影響

- **このまま上げて問題ないか**: はい。今回の変更は本番用の挙動を壊しません。
  - `image_utils` のローカル用 URL 変換は `_is_local_host` 判定のときだけ動作し、本番ホストでは行いません。
  - 称号画像のフォールバック、カード属性・説明、プロフィール投稿全件取得など、いずれも本番でそのまま使えます。
- **注意**: 既存の `backend/.env` や `backend/.env.prod` などは**アップロードしない**でください。サーバー側の環境変数設定を変えてしまいます。

---

## 3. マイグレーションが必要か

**必要です**（まだ `0004` を流していない場合のみ）。

- Card に `attribute` / `atk_points` / `def_points` / `card_type` / `buff_effect` を追加した `0004` が未適用なら、マイグレーションを実行してください。
- 既に `0004` を適用済みなら、マイグレーションは不要です。

### マイグレーションのやり方

**実行場所**: サーバー上の **backend ディレクトリ**（`manage.py` がある場所）。パス例: `/var/www/toybox/backend`。

> 補足: サーバーによっては `python` コマンドが無く、`python3` のみ存在します。  
> その場合は、以下の `python` を **`python3`** に読み替えて実行してください。

1. **未適用かどうか確認する**

   ```bash
   cd /var/www/toybox/backend
   source venv/bin/activate   # venv 運用の場合
   python3 manage.py showmigrations gamification
   ```

   `gamification` の一覧で `0004_add_card_fields_attribute_atk_def_type_buff` の行が **`[ ]`（空白）** なら未適用、**`[X]`** なら適用済みです。

2. **未適用なら実行する**

   ```bash
   python3 manage.py migrate gamification
   ```

   全アプリをまとめて適用する場合は:

   ```bash
   python3 manage.py migrate
   ```

3. **Docker で動かしている場合**

   ```bash
   cd /var/www/toybox
   docker compose exec web python3 manage.py showmigrations gamification   # 確認
   docker compose exec web python3 manage.py migrate gamification          # 実行
   ```

   （`docker-compose` や別名のサービスの場合は、そのコマンドに合わせて `docker compose` の部分を読み替えてください。）

4. **実行後**

   - エラーが出ず `Applying gamification.0004_... OK.` のように出れば成功です。
   - 管理画面のカード一覧で「属性」列などが表示されるようになります。

---

## 4. サーバー上で実行するコマンド

アップロード後、**backend のプロジェクトルート**（`manage.py` があるディレクトリ）で実行します。

### 4.1. ディレクトリへ移動

```bash
cd /var/www/toybox/backend
```

### 4.2. 仮想環境の有効化（venv 運用の場合）

```bash
source venv/bin/activate
```

### 4.3. マイグレーション（未適用なら実行）

```bash
python3 manage.py migrate
# もしくは gamification だけ
python3 manage.py migrate gamification
```

### 4.4. 静的ファイルの collect（本番で Django が static を配信する場合）

```bash
python3 manage.py collectstatic --noinput
```

※ Nginx/Caddy 等で `STATIC_ROOT` を配信している場合は必須です。配信構成に合わせて実行してください。

### 4.5. 称号画像の初期化（任意）

称号マスターに画像を紐付け、未配置時はデフォルト画像を使うようにする場合：

```bash
python3 manage.py init_titles
```

- `MEDIA_ROOT/titles/` に画像が無い称号に対して、`frontend/static/.../hero/toybox-title.png` をコピーして `image_url` を設定します。
- 既に `init_titles` を実行済みで、追加の称号も同じ仕様にしたい場合に再実行すれば問題ありません。

### 4.6. アプリの再起動

**A. systemd で Django を動かしている場合**

```bash
sudo systemctl restart toybox-backend
# サービス名が違う場合は適宜変更
```

**B. Docker Compose で動かしている場合**

コードが**イメージに含まれる**構成なら、WinSCP で置いたファイルを反映するには再ビルドが必要です。

```bash
cd /var/www/toybox

docker compose -f docker-compose.yml -f docker-compose.prod.yml build web
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d web
```

worker / beat も同じイメージを使っている場合は、あわせて再ビルド・再起動してください。

**C. 手動で gunicorn 等を起動している場合**

```bash
# 既存プロセスを止めてから再起動
pkill -f gunicorn
# 起動コマンドはこれまでの運用に合わせて実行
```

---

## 5. デプロイ後の確認

1. **管理画面**
   - カード一覧で「属性」が色付きで表示されるか
   - 称号一覧でバナー画像が表示されるか（`init_titles` 実行済みなら）

2. **コレクション**
   - 属性の色分け・アウトラインがつくか
   - カードホバーで説明ツールチップが出るか

3. **プロフィール**
   - 他ユーザー／自分のプロフィールで、提出一覧が全件表示されるか

4. **マイページ**
   - 投稿画像・称号・取得カードが表示されるか（従来どおり）

---

## 6. まとめチェックリスト

- [ ] 上記ファイルを WinSCP でサーバーにアップロード
- [ ] `python3 manage.py migrate`（または `migrate gamification`）を実行
- [ ] 必要なら `collectstatic` を実行
- [ ] 必要なら `init_titles` を実行
- [ ] Web アプリ（systemd / Docker / gunicorn）を再起動
- [ ] 上記「デプロイ後の確認」を実施

---

## 7. トラブル時

- **管理画面で `attribute` がない等の DB エラー**  
  → `0004` のマイグレーションが未適用の可能性。`migrate` を実行してください。

- **称号画像が表示されない**  
  → `init_titles` を実行し、`MEDIA_ROOT/titles/` に画像ができるか確認してください。

- **変更が反映されない**  
  → アプリの再起動（場合によりイメージ再ビルド）を行ったか確認してください。
