variable "region" {
  default = "us-east-1"
}

variable "ami" {
  default = "ami-0e2c8caa4b6378d8c"
}

variable "key_name" {
  description = "Nombre de la llave SSH para acceder a la instancia"
  type        = string
  default     = "TerraformBack"
}