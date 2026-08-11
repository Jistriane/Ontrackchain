## ============================================================
## Terraform: CMK SOPS envelope encryption + S3 WORM Object Lock
## LGPD Art.49 §6, §8 ; BACEN Circular 3.990 Art.32
## Idempotente 100% (force_destroy desabilitado no CMK)
## ============================================================
terraform {
  required_version = ">= 1.9.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.80.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
  default_tags {
    tags = {
      Project     = "Ontrackchain"
      Environment = var.environment
      Compliance  = "LGPD-ART49-S6;BACEN-CIRC3990-ART32"
      ManagedBy   = "terraform"
    }
  }
}

variable "environment" { type = string; default = "staging"; description = "staging/production-canary/production" }
variable "rotar_cmk_em_dias" { type = number; default = 365; description = "Auto-rotation AWS KMS CMK SOPS (padrão 1a LGPD §57)" }
variable "worm_retention_months" { type = number; default = 120; description = "WORM Object Lock: 120 meses = 10 anos (BACEN Circular 3990 §32 IV)" }
variable "enable_s3_versioning_suspend" { type = bool; default = false; description = "Só true em P0 incidente LGPD Art.55 §3 (dano iminente)" }

## -----------------------------
## KMS CMK Multi-Tenant SOPS
## -----------------------------
resource "aws_kms_key" "sops_envelope_multi_tenant" {
  description                 = "CMK envelope encryption SOPS: 14 secrets Helm (.env-*) + DB credenciais rotacionadas"
  key_usage                   = "ENCRYPT_DECRYPT"
  customer_master_key_spec    = "SYMMETRIC_DEFAULT"
  rotation_period_in_days     = var.rotar_cmk_em_dias
  deletion_window_in_days     = 90
  enable_key_rotation         = true
  multi_region                = false
  is_enabled                  = true
  policy                      = data.aws_iam_policy_document.sops_cmk_policy.json
  lifecycle {
    prevent_destroy = true
    ignore_changes = [tags]
  }
}

data "aws_iam_policy_document" "sops_cmk_policy" {
  ## Root sempre como principal fallback (melhor prática AWS)
  statement {
    sid = "EnableRootAdmin"
    principals { type = "AWS"; identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"] }
    actions   = ["kms:*"]
    resources = ["*"]
    effect    = "Allow"
  }
  statement {
    sid = "AllowKeyUserRoleEncryptionDecryption"
    principals { type = "AWS"; identifiers = var.key_user_role_arns }
    actions = [
      "kms:Encrypt", "kms:Decrypt", "kms:ReEncrypt*",
      "kms:GenerateDataKey*", "kms:DescribeKey"
    ]
    resources = ["*"]
    effect = "Allow"
  }
  statement {
    sid = "DenyUnauthorizedUsageFromOutsideProdAccount"
    principals = { type = "*"; identifiers = ["*"] }
    actions    = ["kms:Encrypt", "kms:Decrypt"]
    resources  = ["*"]
    effect     = "Deny"
    condition {
      test     = "StringNotEquals"
      variable = "aws:PrincipalAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

variable "key_user_role_arns" {
  type = list(string)
  default = []
  description = "ARNs IAM Roles autorizadas usar CMK SOPS: CI/CD CD bot + operador M5 (4-olhos)"
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

resource "aws_kms_alias" "sops_cmk_alias" {
  name          = "alias/ontrackchain-sops-cmk-${var.environment}"
  target_key_id = aws_kms_key.sops_envelope_multi_tenant.key_id
  lifecycle { prevent_destroy = true }
}

## -----------------------------
## S3 Bucket WORM Object Lock 120 meses
## -----------------------------
resource "aws_s3_bucket" "ontrackchain_worm_compliance" {
  bucket = "ontrackchain-worm-compliance-${var.environment}-${data.aws_caller_identity.current.account_id}-${data.aws_region.current.name}"
  tags = {
    ComplianceLevel = "BACEN-C3990-10ANOS"
    WormRetencion   = "${var.worm_retention_months}mo"
    LGPD            = "Art52-DadoSensivel-Retenção"
  }
  force_destroy = false
  object_lock_enabled = true
}

resource "aws_s3_bucket_versioning" "worm_ver" {
  bucket = aws_s3_bucket.ontrackchain_worm_compliance.id
  versioning_configuration {
    status = var.enable_s3_versioning_suspend ? "Suspended" : "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "worm_sse" {
  bucket = aws_s3_bucket.ontrackchain_worm_compliance.id
  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.sops_envelope_multi_tenant.arn
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "worm_public_block" {
  bucket = aws_s3_bucket.ontrackchain_worm_compliance.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_object_lock_configuration" "worm_lock" {
  bucket = aws_s3_bucket.ontrackchain_worm_compliance.id
  rule {
    default_retention {
      mode  = "COMPLIANCE"  # modo BACEN LGPD: NENHUM user (nem root) pode apagar antes do prazo
      days  = 0
      years = floor(var.worm_retention_months / 12)  # 120mo => 10 anos
    }
  }
}

resource "aws_s3_bucket_object_lock_configuration" "worm_lock_extra_months" {
  count = (var.worm_retention_months % 12) > 0 ? 1 : 0
  bucket = aws_s3_bucket.ontrackchain_worm_compliance.id
  # bucket-level default rule é por anos; aplicações podem definir modo dias via header x-amz-object-lock-retain-until-date
}

resource "aws_s3_bucket_logging" "worm_access_logs" {
  bucket = aws_s3_bucket.ontrackchain_worm_compliance.id
  target_bucket = aws_s3_bucket.ontrackchain_worm_logs.id
  target_prefix = "s3-worm-access/"
}

resource "aws_s3_bucket" "ontrackchain_worm_logs" {
  bucket = "ontrackchain-worm-logs-${var.environment}-${data.aws_caller_identity.current.account_id}-${data.aws_region.current.name}"
  object_lock_enabled = true
  force_destroy = false
  tags = { Role = "AccessLogBucket", Retention = "365d" }
}

resource "aws_s3_bucket_object_lock_configuration" "worm_logs_lock" {
  bucket = aws_s3_bucket.ontrackchain_worm_logs.id
  rule {
    default_retention {
      mode = "COMPLIANCE"
      days = 365
    }
  }
}
resource "aws_s3_bucket_public_access_block" "worm_logs_block" {
  bucket = aws_s3_bucket.ontrackchain_worm_logs.id
  block_public_acls = true; block_public_policy = true; ignore_public_acls = true; restrict_public_buckets = true
}
resource "aws_s3_bucket_versioning" "worm_logs_ver" {
  bucket = aws_s3_bucket.ontrackchain_worm_logs.id
  versioning_configuration { status = "Enabled" }
}

## -----------------------------
## Outputs para consumo em .env-prod
## -----------------------------
output "sops_cmk_arn" { value = aws_kms_key.sops_envelope_multi_tenant.arn; description = "ARN CMK p/ SOPS create-env-file: --kms arn:..." }
output "sops_cmk_alias" { value = aws_kms_alias.sops_cmk_alias.name }
output "worm_bucket" { value = aws_s3_bucket.ontrackchain_worm_compliance.bucket; description = "WORM Object Lock compliance 120m (put obj com x-amz-object-lock-mode COMPLIANCE para override)" }
output "worm_logs_bucket" { value = aws_s3_bucket.ontrackchain_worm_logs.bucket }
output "cmk_rotation_days" { value = var.rotar_cmk_em_dias }
