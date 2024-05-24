Lambda Quota
https://docs.aws.amazon.com/ja_jp/lambda/latest/dg/gettingstarted-limits.html

payloadサイズ：最大6MB


## 初期設定

```
pip install aws-sam-cli
```

## ローカル環境でテスト実行する

```
sam build && sam local invoke Synthetics --event sample.json
```

## Lambdaにデプロイする

```
sam build

# 初回のみ
sam deploy --guided

# ２回目以降
sam deploy
```

--guidedオプションを付けると設定ファイルが作成される。
２回目以降は設定ファイルの項目に従って実行される


## lambdaを実行する
初回デプロイ時に指定したstack-nameを指定
```
sam remote invoke --stack-name Synthetics --event-file sample.json
```

## リソース全削除

```
sam delete
```
