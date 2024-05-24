FROM python:3.8-slim

# Lambdaライブラリを追加
RUN apt-get update && apt-get install -y \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 必要な依存関係をインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Lambda関数のコードをコピー
COPY lambda_function.py .

# Lambdaエントリポイント
CMD ["lambda_function.lambda_handler"]

