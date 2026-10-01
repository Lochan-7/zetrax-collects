# 🎴 Zetrax Collects

> A full-stack serverless web application on AWS: open randomized Pokémon TCG packs with weighted rarity, persistent pull history, and a global CDN frontend.

🔗 **Live demo:** https://du5gcfk2zq914.cloudfront.net
📱 **Content channels:** [YouTube](https://youtube.com/@zetraxcollects) · [Instagram](https://www.instagram.com/zetrax_collects) · [TikTok](https://www.tiktok.com/@zetraxcollects)

---

## 📸 Preview

Visit the live link above or add a `screenshot.png` to `docs/` and reference it here.

---

## 🏗️ Architecture

```
┌─────────────┐
│   Visitor   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────┐
│  CloudFront (HTTPS CDN) │
└──────┬──────────────────┘
       │
       ├─────► Static assets
       │        ▼
       │   ┌─────────────────┐
       │   │  S3 (frontend)  │
       │   └─────────────────┘
       │
       └─────► Dynamic requests
                ▼
           ┌─────────────────┐
           │  API Gateway    │
           │  (HTTP API v2)  │
           └────────┬────────┘
                    ▼
           ┌─────────────────┐
           │  Lambda         │
           │  (Python 3.12)  │
           └────────┬────────┘
                    ▼
           ┌─────────────────┐
           │  DynamoDB       │
           │ (pack history)  │
           └─────────────────┘
```

| Component | AWS Service | Purpose |
|---|---|---|
| Static hosting | **S3** | Serves `index.html`, `banner.jpg` |
| CDN + HTTPS | **CloudFront** | Global edge caching, free TLS certificate, HTTP→HTTPS redirect |
| HTTP API | **API Gateway (v2)** | Routes requests to Lambda, handles CORS |
| Compute | **Lambda (Python 3.12)** | Weighted-random pack simulation + DynamoDB persistence |
| Database | **DynamoDB** | Pack history, pay-per-request, serverless |
| Permissions | **IAM** | Least-privilege execution role + custom inline policy for DynamoDB |

---

## ⚡ Features

- 🎴 **Realistic pack simulation** — 20 cards across 6 rarities (Common 55%, Uncommon 25%, Rare 13%, Ultra Rare 5%, Secret Rare 1.5%, Chase 0.5%)
- 💾 **Persistent history** — every opened pack saved to DynamoDB, latest 8 shown on page
- 🎨 **Animated UI** — card reveal animations, rarity-based glows (chase cards get a gold pulsing border)
- 🔒 **HTTPS everywhere** — CloudFront terminates TLS; S3 origin served over HTTP internally
- 📱 **Works in any browser** including in-app WhatsApp/Instagram/TikTok browsers (thanks to CloudFront)
- 🌐 **CORS-enabled API** — frontend can be hosted anywhere
- 🤖 **Fully serverless** — zero servers to manage, scales to zero when idle

---

## 📁 Project Structure

```
zetrax-collects/
├── README.md
├── .gitignore
├── frontend/
│   ├── index.html           # Vanilla HTML/CSS/JS
│   └── banner.jpg           # Hero banner
├── lambda/
│   └── lambda_function.py   # Pack opener + DynamoDB handler
├── iam/
│   ├── lambda-trust.json    # Trust policy (Lambda service → assume role)
│   └── dynamo-policy.json   # Least-privilege DynamoDB access
└── docs/
    └── (optional screenshots, architecture diagrams)
```

---

## 🚀 Deploy It Yourself

### Prerequisites
- AWS account with CLI configured (`aws configure`)
- Region: `ap-southeast-1` (adjust if desired)
- Python 3.12 (for Lambda packaging)

### 1. Create the DynamoDB table

```bash
aws dynamodb create-table \
  --table-name zetrax-pack-history \
  --attribute-definitions AttributeName=pack_id,AttributeType=S \
  --key-schema AttributeName=pack_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region ap-southeast-1
```

### 2. Create the IAM role for Lambda

```bash
aws iam create-role --role-name zetrax-pack-role \
  --assume-role-policy-document file://iam/lambda-trust.json

aws iam attach-role-policy --role-name zetrax-pack-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam put-role-policy --role-name zetrax-pack-role \
  --policy-name DynamoDBAccess \
  --policy-document file://iam/dynamo-policy.json
```

> ⚠️ Update the account ID / region in `iam/dynamo-policy.json` first.

### 3. Deploy the Lambda

```bash
cd lambda
zip -r ../function.zip lambda_function.py
cd ..

aws lambda create-function --function-name zetrax-pack-opener \
  --runtime python3.12 \
  --role arn:aws:iam::YOUR_ACCOUNT:role/zetrax-pack-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://function.zip \
  --region ap-southeast-1
```

### 4. Create the API Gateway

```bash
aws apigatewayv2 create-api \
  --name zetrax-pack-api \
  --protocol-type HTTP \
  --target arn:aws:lambda:ap-southeast-1:YOUR_ACCOUNT:function:zetrax-pack-opener \
  --cors-configuration AllowOrigins="*",AllowMethods="GET",AllowHeaders="Content-Type" \
  --region ap-southeast-1
```

Grant API Gateway permission to invoke the Lambda:

```bash
aws lambda add-permission --function-name zetrax-pack-opener \
  --statement-id APIGatewayInvoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:ap-southeast-1:YOUR_ACCOUNT:API_ID/*/*" \
  --region ap-southeast-1
```

### 5. Deploy the frontend

Update the `API_BASE` constant at the bottom of `frontend/index.html` with your API Gateway URL, then:

```bash
aws s3 mb s3://your-bucket-name --region ap-southeast-1
aws s3 website s3://your-bucket-name/ --index-document index.html
# (apply public-read bucket policy)
aws s3 cp frontend/index.html s3://your-bucket-name/
aws s3 cp frontend/banner.jpg s3://your-bucket-name/
```

### 6. (Optional) Add CloudFront for HTTPS

Create a distribution with the S3 website endpoint as origin:
- Origin type: **Custom (Other)**
- Origin protocol: **HTTP Only**
- Viewer protocol: **Redirect HTTP to HTTPS**
- Default root object: `index.html`

---

## 🧠 Key Design Decisions

**Why DynamoDB instead of RDS?** Pack history is a simple key-value lookup pattern. DynamoDB gives single-digit ms latency with no server to manage. SQL would be overkill.

**Why API Gateway instead of Lambda Function URL?** Function URLs had persistent auth issues on this account; API Gateway offers more features (routing, CORS management, future custom domain) and is production-standard.

**Why CloudFront in front of S3?** S3 static website hosting is HTTP-only. CloudFront provides free HTTPS via its default `*.cloudfront.net` certificate, plus global edge caching. WhatsApp/Instagram in-app browsers refuse HTTP links — CloudFront fixes this.

**Why `--billing-mode PAY_PER_REQUEST` on DynamoDB?** No capacity planning needed for low-traffic learning apps. Scales from zero without warm-up.

**Why custom inline IAM policy instead of `AmazonDynamoDBFullAccess`?** Least privilege. The Lambda only needs `PutItem` and `Scan` on one specific table.

---

## 🛠️ Tech Stack

**Languages:** Python 3.12 · HTML5 · CSS3 · JavaScript (ES6+)
**AWS Services:** S3 · CloudFront · API Gateway · Lambda · DynamoDB · IAM · CloudWatch Logs
**Tools:** AWS CLI · PowerShell

---

## 📊 What I Learned Building This

- Serverless architecture tradeoffs (cold starts, 15-min timeout, cost model)
- CORS debugging across API Gateway + Lambda response headers
- CloudFront origin configuration (S3 website vs REST endpoints)
- DynamoDB's AttributeValue format and item flexibility
- IAM least-privilege policies via inline role policies
- CloudFront cache invalidation and browser cache behavior

---

## 📜 License

MIT. Use freely.

---

*Built as part of a hands-on AWS learning project. Open to feedback.*
