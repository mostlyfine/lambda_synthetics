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
aws ecr get-login-password  | docker login --username AWS --password-stdin <AWSアカウントID>.dkr.ecr.ap-northeast-1.amazonaws.com
docker tag helloworldfunction:python3.8-v1 <AWSアカウントID>.dkr.ecr.ap-northeast-1.amazonaws.com/helloworldfunction:python3.8-v1
docker push <AWSアカウントID>.dkr.ecr.ap-northeast-1.amazonaws.com/helloworldfunction:python3.8-v1

sam build
sam deploy --guided
```


## lambdaをローカルから実行する

```
sam invoke --payload fileb://payload.json
```


