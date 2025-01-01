output "servers_status" {
  value = {
    for server in hcloud_server.podman :
    server.name => server.status
  }
}

output "servers_ips" {
  value = {
    for server in hcloud_server.podman :
    server.name => server.ipv4_address
  }
}

output "volume_ids" {
  value = {
    for volume in hcloud_volume.podman_server_volume :
    volume.name => volume.id
  }
}
