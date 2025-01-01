resource "hcloud_firewall" "limit_ssh" {
  count = 0
  name = "allow-my-ip-only"

  rule {
    direction = "in"
    protocol  = "tcp"
    port      = "22"
    source_ips = [
      "${var.my_ip_address}/32"
    ]
  }
}

resource "hcloud_firewall_attachment" "example" {
  firewall_id = hcloud_firewall.limit_ssh.id
  server_ids  = [hcloud_server.podman.id]
}
