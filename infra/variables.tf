variable "subscription_id" {
  type = string
}

variable "resource_group_name" {
  type = string
}

variable "env_resource_group_name" {
  type = string
}

variable "create_shared_resources" {
  type    = bool
  default = true
}

variable "location" {
  type = string
}

variable "container_app_environment_name" {
  type = string
}

variable "env" {
  type    = string
  default = "testbed"
}

variable "registry_server" {
  type    = string
  default = "ghcr.io/v03051435"
}

variable "registry_host" {
  type    = string
  default = "ghcr.io"
}

variable "registry_username" {
  type = string
}

variable "registry_password_secret_name" {
  type    = string
  default = "ghcrio-v03051435"
}

variable "registry_password" {
  type      = string
  sensitive = true
}

variable "image_tag" {
  type = string
}

variable "workload_profile_name" {
  type    = string
  default = "Consumption"
}

variable "workload_profile_type" {
  type    = string
  default = "Consumption"
}

variable "workload_profile_minimum" {
  type    = number
  default = 0
}

variable "workload_profile_maximum" {
  type    = number
  default = 0
}

variable "max_inactive_revisions" {
  type    = number
  default = 100
}

variable "log_analytics_workspace_name" {
  type = string
}

variable "log_analytics_workspace_sku" {
  type    = string
  default = "PerGB2018"
}

variable "log_analytics_retention_in_days" {
  type    = number
  default = 30
}
