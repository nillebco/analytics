resource "hcloud_server" "podman" {
  count       = var.instances
  name        = "podman-server-${count.index}"
  image       = var.os_type
  server_type = var.server_type
  location    = var.location
  ssh_keys    = [hcloud_ssh_key.default.id]
  labels = {
    type = "podman-server"
  }
  user_data = templatefile("user_data.yml", {
    VOLUME_ID = hcloud_volume.podman_server_volume[count.index].id
  })
}
