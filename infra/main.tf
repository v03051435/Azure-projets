terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 3.100.0"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

resource "azurerm_resource_group" "env_rg" {
  count    = var.create_shared_resources ? 1 : 0
  name     = var.env_resource_group_name
  location = var.location
}

data "azurerm_resource_group" "env_rg" {
  count = var.create_shared_resources ? 0 : 1
  name  = var.env_resource_group_name
}

resource "azurerm_resource_group" "app_rg" {
  count    = var.resource_group_name == var.env_resource_group_name ? 0 : 1
  name     = var.resource_group_name
  location = var.location
}

resource "azurerm_log_analytics_workspace" "law" {
  count               = var.create_shared_resources ? 1 : 0
  name                = var.log_analytics_workspace_name
  location            = var.location
  resource_group_name = local.env_rg_name
  sku                 = var.log_analytics_workspace_sku
  retention_in_days   = var.log_analytics_retention_in_days
}

data "azurerm_log_analytics_workspace" "law" {
  count               = var.create_shared_resources ? 0 : 1
  name                = var.log_analytics_workspace_name
  resource_group_name = local.env_rg_name
}

resource "azurerm_container_app_environment" "env" {
  count                         = var.create_shared_resources ? 1 : 0
  name                          = var.container_app_environment_name
  location                      = var.location
  resource_group_name           = local.env_rg_name
  log_analytics_workspace_id    = local.log_analytics_workspace_id

  workload_profile {
    name                  = var.workload_profile_name
    workload_profile_type = var.workload_profile_type
    minimum_count         = var.workload_profile_minimum
    maximum_count         = var.workload_profile_maximum
  }
}

data "azurerm_container_app_environment" "env" {
  count               = var.create_shared_resources ? 0 : 1
  name                = var.container_app_environment_name
  resource_group_name = local.env_rg_name
}

locals {
  env_rg_name = var.env_resource_group_name
  env_rg_id = var.create_shared_resources ? azurerm_resource_group.env_rg[0].id : data.azurerm_resource_group.env_rg[0].id
  app_rg_name = var.resource_group_name == var.env_resource_group_name ? local.env_rg_name : azurerm_resource_group.app_rg[0].name
  app_rg_id = var.resource_group_name == var.env_resource_group_name ? local.env_rg_id : azurerm_resource_group.app_rg[0].id
  log_analytics_workspace_id = var.create_shared_resources ? azurerm_log_analytics_workspace.law[0].id : data.azurerm_log_analytics_workspace.law[0].id
  container_app_environment_id = var.create_shared_resources ? azurerm_container_app_environment.env[0].id : data.azurerm_container_app_environment.env[0].id
}

locals {
  services_json = jsondecode(file("${path.module}/../pipelines/services.json"))
  services      = try(local.services_json.services, {})

  env_services = {
    for name, svc in local.services : name => {
      repo           = try(svc.repo, "")
      app_name       = try(svc.deploy[var.env].appName, "")
      container_name = try(svc.deploy[var.env].appName, "")
      target_port    = try(svc.deploy[var.env].targetPort, 8080)
      env_list = [
        for pair in try(svc.deploy[var.env].envVars, []) : {
          name  = split("=", pair)[0]
          value = join("=", slice(split("=", pair), 1, length(split("=", pair))))
        } if trimspace(pair) != ""
      ]
    }
    if(
      try(svc.skip, false) == false &&
      try(svc.deploy[var.env].skip, false) == false &&
      try(svc.deploy[var.env].appName, "") != "" &&
      try(svc.repo, "") != ""
    )
  }
}

resource "azurerm_container_app" "app" {
  for_each                     = local.env_services
  name                         = each.value.app_name
  resource_group_name          = local.app_rg_name
  container_app_environment_id = local.container_app_environment_id
  revision_mode                = "Single"

  secret {
    name  = var.registry_password_secret_name
    value = var.registry_password
  }

  registry {
    server               = var.registry_host
    username             = var.registry_username
    password_secret_name = var.registry_password_secret_name
  }

  workload_profile_name  = var.workload_profile_name
  max_inactive_revisions = var.max_inactive_revisions

  identity {
    type = "SystemAssigned"
  }

  ingress {
    external_enabled = true
    target_port      = each.value.target_port
    transport        = "auto"

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    container {
      name   = each.value.container_name
      image  = "${var.registry_server}/${each.value.repo}:${var.image_tag}"
      cpu    = 0.5
      memory = "1Gi"

      dynamic "env" {
        for_each = each.value.env_list
        content {
          name  = env.value.name
          value = env.value.value
        }
      }
    }
  }

  lifecycle {
    ignore_changes = [
      registry,
      secret,
      template[0].container[0].image,
    ]
  }
}
