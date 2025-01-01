resource "hcloud_volume" "podman_server_volume" {
  count    = var.instances
  name     = "podman-server-volume-${count.index}"
  size     = var.disk_size
  location = var.location
  format   = "xfs"
}

resource "hcloud_volume_attachment" "web_vol_attachment" {
  count     = var.instances
  volume_id = hcloud_volume.podman_server_volume[count.index].id
  server_id = hcloud_server.podman[count.index].id
  automount = true
}
