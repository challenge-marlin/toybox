# 古いコンテナの停止手順

Django移行前の`toybox`グループのコンテナを停止・削除する手順です。

## 手順

### 1. 古い`toybox`グループのコンテナを停止

ルートディレクトリから実行：

```powershell
cd C:\github\toybox
docker compose down
```

または、Docker DesktopのGUIから：
- `toybox`グループの全てのコンテナを選択
- 「Stop」ボタンをクリック
- 停止後、「Delete」ボタンをクリック

### 2. 新しい`backend`グループのコンテナを起動

`backend`ディレクトリから実行：

```powershell
cd C:\github\toybox\backend
docker compose up -d
```

または：

```powershell
cd C:\github\toybox\backend
make up
```

### 3. 動作確認

- Django API: http://localhost:8000/api/
- Django Admin: http://localhost:8000/admin/
- フロントエンド（Djangoテンプレート）: http://localhost:8000/me/

## 注意事項

- 古いコンテナを削除する前に、必要なデータをバックアップしてください
- MongoDBのデータはDjango移行後は使用されません（PostgreSQLに移行済み）
- ポート競合は発生しません：
  - 古いコンテナ: 3000, 4000
  - 新しいコンテナ: 8000, 5432, 6379

