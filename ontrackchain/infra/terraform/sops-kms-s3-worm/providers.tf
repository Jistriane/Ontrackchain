# Arquivo separado para facilitar upgrade de providers independente de resources.
terraform {
  required_version = ">= 1.9.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.80.0"
      configuration_aliases = [aws.us_east_1]
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6.3"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0.6"
    }
  }
  backend "s3" {
    # Preencher em s3.tfbackend, NÃO aqui (princípio: arquivo fixo no repo, valores separados por ambiente)
    # bucket = "ontrackchain-tfstate-PROD-ACCOUNTID-us-east-1"
    # key    = "sops-kms-s3-worm/terraform.tfstate"
    # region = "us-east-1"
    # encrypt        = true
    # kms_key_id     = "arn:aws:kms:us-east-1:ACCOUNT:key/REPLACE_WITH_STATE_CMK_ARN"
    # dynamodb_table = "ontrackchain-terraform-locks"
    # role_arn       = "arn:aws:iam::ACCOUNT:role/ontrackchain-terraform-runner-4eyes"
  }
}

provider "aws" {
  alias   = "us_east_1"
  region  = "us-east-1"
  profile = var.aws_profile
  assume_role {
    # role_arn = "arn:aws:iam::ACCOUNT:role/ontrackchain-terraform-runner-4eyes"
    session_name = "ontrackchain-sops-kms-worm-terraform"
    duration     = "900s"
  }
  default_tags {
    tags = {
      Project     = "Ontrackchain"
      Environment = var.environment
      Compliance  = "LGPD-ART49-S6;BACEN-CIRC3990-ART32"
      ManagedBy   = "terraform"
      IaCTier     = "S28-9-security-foundation"
    }
  }
}

# Gerador de sufixo determinístico (36 bytes hex) para buckets S3 globais únicos
resource "random_id" "bucket_suffix" {
  byte_length = 8
  keepers = {
    env = var.environment
  }
}
