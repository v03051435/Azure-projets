output "container_app_names" {
  value = {
    for name, app in azurerm_container_app.app : name => app.name
  }
}

output "container_app_fqdns" {
  value = {
    for name, app in azurerm_container_app.app : name => try(app.ingress[0].fqdn, "")
  }
}
