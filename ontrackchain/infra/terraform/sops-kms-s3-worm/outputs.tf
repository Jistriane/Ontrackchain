output "sops_cmk_arn" {
  value       = aws_kms_key.sops_envelope_multi_tenant.arn
  description = "ARN CMK envelope encryption SOPS. Copiar para .sops.yaml creation_rules[].kms e values.yaml global.kmsKeyId"
}

output "sops_cmk_key_id" {
  value       = aws_kms_key.sops_envelope_multi_tenant.key_id
  description = "Key ID (formato UUID) do CMK SOPS — p/ operações CLI kms:"
}

output "sops_cmk_alias" {
  value       = aws_kms_alias.sops_cmk_alias.name
  description = "Alias human-readable p/ referenciar CMK em dashboards e políticas"
}

output "kms_cmk_rotation_days" {
  value       = var.rotar_cmk_em_dias
  description = "Rotação automática AWS KMS. LGPD §57 sugere 1 ano (365 dias)."
}

output "worm_bucket_compliance_name" {
  value       = aws_s3_bucket.ontrackchain_worm_compliance.bucket
  description = "Bucket com WORM Object Lock COMPLIANCE 120 meses. NÃO excluir via console (bloqueado)."
}

output "worm_bucket_compliance_arn" {
  value       = aws_s3_bucket.ontrackchain_worm_compliance.arn
  description = "ARN p/ políticas IAM de escrita restrita (s3:PutObject) apenas otel collector + SRE 4-olhos."
}

output "worm_bucket_logs_name" {
  value = aws_s3_bucket.ontrackchain_worm_logs.bucket
}

output "worm_retention_mode_and_period" {
  value = {
    mode   = "COMPLIANCE"
    years  = floor(var.worm_retention_months / 12)
    months = var.worm_retention_months % 12
  }
  description = "BACEN Circular 3990 Art.32 IV: arquivos mínimos 120 meses COMPLIANCE (nem root pode apagar antes). Saiba mais: https://www.bcb.gov.br/pre/normativos/res/2020/circ_3990.html"
}

output "access_log_target_bucket" {
  value       = aws_s3_bucket.ontrackchain_worm_logs.bucket
  description = "Bucket que recebe S3 Server Access Logs do bucket compliance."
}

output "terraform_s3_backend_template_path" {
  value       = "${path.module}/s3.tfbackend"
  description = "Use como: terraform init -backend-config=s3.tfbackend"
}
