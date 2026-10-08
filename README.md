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
- 🧱 **Infrastructure as code** — the whole stack is defined in Terraform (`terraform/`)

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
│   ├── lambda-trust.json    # Trust policy (kept for reference; Terraform owns the live role)
│   └── dynamo-policy.json   # Inline policy (kept for reference; Terraform owns the live policy)
├── terraform/              # Infrastructure as code — the live deployment
│   ├── versions.tf          # Providers + S3 remote state backend
│   ├── variables.tf
│   ├── main.tf              # DynamoDB, IAM, Lambda, API Gateway
│   ├── frontend.tf          # S3 bucket, website, assets, CloudFront
│   ├── outputs.tf
│   └── README.md
└── docs/
    └── (optional screenshots, architecture diagrams)
```

---

## 🚀 Deploy It Yourself

### Prerequisites
- AWS account with CLI configured (`aws configure`)
- [Terraform](https://developer.hashicorp.com/terraform/install) ≥ 1.10
- Python 3.12 (for Lambda packaging — Terraform zips the source itself)

### Deploy

```bash
cd terraform
terraform init
terraform apply
```

That provisions DynamoDB, IAM, Lambda, API Gateway, S3 and CloudFront in one go. The site URL is printed as the `site_url` output. See [`terraform/README.md`](terraform/README.md) for details, including how to point the backend at your own state bucket.

### Day-two updates

- **Lambda code:** edit `lambda/lambda_function.py` and run `terraform apply`.
- **Frontend:** edit anything under `frontend/` and run `terraform apply`. For a fresh copy immediately, invalidate CloudFront: `aws cloudfront create-invalidation --distribution-id $(terraform -chdir=terraform output -raw cloudfront_distribution_id) --paths '/*'`.

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
