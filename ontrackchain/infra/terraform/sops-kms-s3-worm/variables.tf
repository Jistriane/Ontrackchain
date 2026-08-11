variable "aws_profile" { type = string; default = "ontrackchain-prod"; description = "Profile ~/.aws/credentials (4-olhos ou IAM OIDC CI role)" }
variable "environment" { type = string; default = "staging"; description = "staging/production-canary/production (M5 environements MGD)" }
variable "rotar_cmk_em_dias" { type = number; default = 365; description = "Auto-rotation AWS KMS CMK SOPS (padrão 1a LGPD §57)" }
variable "worm_retention_months" { type = number; default = 120; description = "WORM Object Lock: 120 meses = 10 anos (BACEN Circular 3990 §32 IV)" }
variable "enable_s3_versioning_suspend" { type = bool; default = false; description = "Só true em P0 incidente LGPD Art.55 §3 (dano iminente). Default: false bloquear." }
variable "key_user_role_arns" {
  type = list(string)
  default = []
  description = "ARNs IAM autorizados a usar CMK SOPS: CI runner + 2 SRE 4-olhos + 1 DPO. Mínimo 3 roles recomendado."
}
variable "s3_force_destroy_on_destroy" { type = bool; default = false; description = "Anti-padrão; só true em ambientes throwaway QA. Em prod: false (block)." }
