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
| `backend/gamification/models.py` | `/var/www/toybox/backend/gamification/models.py` |
| `backend/gamification/admin.py` | `/var/www/toybox/backend/gamification/admin.py` |
| `backend/gamification/management/commands/init_titles.py` | `/var/www/toybox/backend/gamification/management/commands/init_titles.py` |
| `backend/frontend/templates/frontend/collection.html` | `/var/www/toybox/backend/frontend/templates/frontend/collection.html` |
| `backend/frontend/templates/frontend/profile_view.html` | `/var/www/toybox/backend/frontend/templates/frontend/profile_view.html` |

**カードの属性・説明を表示する場合**（コレクション・管理画面で属性色やツールチップを出したいとき）は、以下もアップロードしてから「4.5 カードマスタの投入」を実行してください。

| ローカルパス | サーバー側の配置先 |
|-------------|-------------------|
| `backend/src/data/card_master.tsv` | `/var/www/toybox/backend/src/data/card_master.tsv` |

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

### 4.5. カードマスタの投入（属性・説明を反映する場合）

コレクションや管理画面で**属性の色分け・アウトライン**や**カード説明のツールチップ**を表示するには、DB のカードマスタに属性・説明が入っている必要があります。本番で一度も `load_card_master` を流していない、または古い TSV のままの場合は、以下を実行してください。

1. **TSV をサーバーに置く**  
   上記「1. WinSCPでアップロードするファイル」の **カードの属性・説明を表示する場合** で、`backend/src/data/card_master.tsv` をアップロード済みであること。

2. **backend をカレントにしたうえで実行**（venv 運用の場合）

   ```bash
   cd /var/www/toybox/backend
   source venv/bin/activate
   python3 manage.py load_card_master --tsv-file src/data/card_master.tsv
   ```

   **Docker で動かしている場合**（コンテナ名が `web` のとき）

   - **`web` が起動中なら**（`docker compose ps` で web が up のとき）:
     ```bash
     cd /var/www/toybox
     docker compose exec web python3 manage.py load_card_master --tsv-file src/data/card_master.tsv
     ```
   - **`service "web" is not running` と出るとき**は、起動中のコンテナではなく**一時コンテナ**で実行します。  
     **重要**: `web` のイメージは `backend/` をビルドコンテキストにしているため、**backend ディレクトリで** compose を実行してください。  
     `manage.py` が無い・`can't open file '/app/manage.py'` と出る場合は、`cd /var/www/toybox/backend` にしてから実行します。
     ```bash
     cd /var/www/toybox/backend
     docker compose run --rm web python3 manage.py load_card_master --tsv-file src/data/card_master.tsv
     ```
     本番で compose をルート（`/var/www/toybox`）から `-f backend/docker-compose.yml` で呼んでいる場合は、そのまま `-f` を付けて実行しますが、**web のビルドコンテキストが backend になるよう**、実行時のカレントか `--project-directory` で backend を指定してください。

   成功すると、既存カードは `attribute` / `description` 等で上書き更新され、コレクション・管理画面に属性・説明が反映されます。

### 4.6. 称号画像の初期化（任意）

称号マスターに画像を紐付け、未配置時はデフォルト画像を使うようにする場合：

```bash
python3 manage.py init_titles
```

- `MEDIA_ROOT/titles/` に画像が無い称号に対して、`frontend/static/.../hero/toybox-title.png` をコピーして `image_url` を設定します。
- 既に `init_titles` を実行済みで、追加の称号も同じ仕様にしたい場合に再実行すれば問題ありません。

### 4.7. アプリの再起動

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
- [ ] **属性・説明を表示する場合**: `backend/src/data/card_master.tsv` をアップロードし、`load_card_master --tsv-file src/data/card_master.tsv` を実行
- [ ] 必要なら `init_titles` を実行
- [ ] Web アプリ（systemd / Docker / gunicorn）を再起動
- [ ] 上記「デプロイ後の確認」を実施

---

## 7. トラブル時

- **管理画面で `attribute` がない等の DB エラー**  
  → `0004` のマイグレーションが未適用の可能性。`migrate` を実行してください。

- **管理画面のカードに「属性」「ATK」「DEF」「カード種類」「バフ効果」「説明」の欄が出ない**  
  → **models.py** と **admin.py** の両方が本番に反映されていない可能性があります。上記「1. WinSCPでアップロードするファイル」のとおり、`backend/gamification/models.py` と `backend/gamification/admin.py` をサーバーに再アップロードし、Web アプリを再起動してください。マイグレーション `0004` が未適用の場合は `migrate` も実行してください。

- **称号画像が表示されない**  
  → `init_titles` を実行し、`MEDIA_ROOT/titles/` に画像ができるか確認してください。

- **変更が反映されない**  
  → アプリの再起動（場合によりイメージ再ビルド）を行ったか確認してください。

- **カードの属性・説明が表示されない**  
  → 本番DBのカードマスタに属性・説明が入っていない可能性があります。`backend/src/data/card_master.tsv` をサーバーに置き、`load_card_master` を実行してください。Docker で `service "web" is not running` と出る場合は、`docker compose run --rm web python3 manage.py load_card_master --tsv-file src/data/card_master.tsv` を使います（本番用 compose のときは `-f docker-compose.yml -f docker-compose.prod.yml` を付ける）。

- **card_master.tsv がデータベースに読み込まれていない**  
  → まず **TSV がコンテナから見えているか** 確認してください。  
  1) **ホストにファイルがあるか**: `ls -la /var/www/toybox/backend/src/data/card_master.tsv`  
  2) **コンテナ内で見えるか**: `docker compose exec web ls -la /app/src/data/card_master.tsv`  
  無い場合は、WinSCP で `backend/src/data/card_master.tsv` を `/var/www/toybox/backend/src/data/` にアップロード（`src/data/` がない場合はフォルダを作成）。  
  3) **load_card_master 実行時**に「Reading TSV from: /app/src/data/card_master.tsv」と出るか、続けて「Updated: C004 ...」などが出るか確認。  
  4) 「TSV file not found」と出る場合は、**絶対パス**で試す:  
  `docker compose exec web python3 manage.py load_card_master --tsv-file /app/src/data/card_master.tsv`  
  それでも無い場合は、**ホストの TSV をコンテナの /tmp にコピー**してから実行（コンテナIDは `docker compose ps -q web` で確認）:  
  `docker cp /var/www/toybox/backend/src/data/card_master.tsv $(docker compose ps -q web):/tmp/card_master.tsv`  
  `docker compose exec web python3 manage.py load_card_master --tsv-file /tmp/card_master.tsv`

- **`Bind for 0.0.0.0:6379 failed: port is already allocated`**  
  → ホストの 6379 番が別プロセス（別の Redis や古いコンテナ）で使われています。**どのプロセスか確認する**: `sudo ss -tlnp | grep 6379` または `sudo lsof -i :6379`。  
  **Docker の Redis が残っている場合**: `docker ps -a | grep redis` でコンテナ名を確認し、`docker stop <コンテナ名またはID>` で止めてから、再度 `docker compose run --rm web ...` を実行してください。  
  止めた Redis が同じ toybox 用であれば、後で `docker compose up -d` などで再度起動すれば問題ありません。

- **`python3: can't open file '/app/manage.py': No such file or directory`**  
  → compose を**backend ディレクトリ**で実行していないと、コンテナ内の `/app` に `manage.py` がありません。**backend に移動してから**実行してください:  
  `cd /var/www/toybox/backend && docker compose run --rm web python3 manage.py load_card_master --tsv-file src/data/card_master.tsv`

- **`Failed to load resource: the server responded with a status of 500`**（500 エラー）  
  → サーバー側で例外が起いています。**原因を調べる**には、まず **Web コンテナのログ** を確認してください:  
  `docker compose logs web --tail=100`（実行場所は `cd /var/www/toybox/backend` のうえで）。  
  よくある原因の例:  
  1. **DB のカラム不足**（例: `attribute` がない）→ `migrate gamification` を実行。  
  2. **インポートエラー・構文エラー**（アップロードした Python に typo や改行のずれ）→ 該当ファイルを再アップロード、またはローカルで構文チェック。  
  3. **本番で DEBUG=False** のため画面上は「500」だけ→ 上記ログにトレースバックが出ているので、その末尾の **Exception の種類とメッセージ** を見て対処してください。
