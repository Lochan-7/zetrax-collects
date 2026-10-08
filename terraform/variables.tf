variable "region" {
  description = "AWS region for all regional resources."
  type        = string
  default     = "ap-southeast-1"
}

variable "name_prefix" {
  description = "Prefix for resource names."
  type        = string
  default     = "zetrax"
}

variable "frontend_bucket_name" {
  description = "Existing S3 bucket holding the frontend."
  type        = string
  default     = "zetrax-collects"
}

variable "lambda_runtime" {
  type    = string
  default = "python3.12"
}
