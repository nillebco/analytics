variable "hcloud_token" {
  sensitive = true
}

variable "location" {
  default = "nbg1"
}

variable "http_protocol" {
  default = "http"
}

variable "http_port" {
  default = "80"
}

variable "instances" {
  default = "1"
}

variable "server_type" {
  default = "cax11"
}

variable "os_type" {
  default = "ubuntu-24.04"
}

variable "disk_size" {
  default = "20"
}

variable "ip_range" {
  default = "10.0.1.0/24"
}

variable "ipv6_only" {
  default = "20"
}

variable "my_ip_address" {
  default = "121.169.241.38"
}

variable "cloudflare_api_token" {
  sensitive = true
}

variable "cloudflare_account_id" {
}

variable "domain_name" {
}

variable "ssh_key_path" {
  default = "~/.ssh/id_rsa.pub"
}
