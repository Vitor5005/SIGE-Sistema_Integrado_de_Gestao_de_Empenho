#!/bin/bash
# Prepara uma instância EC2 Amazon Linux 2023 para rodar o SIGE com Docker Compose.
# Uso (na instância, como ec2-user):  bash scripts/aws/preparar-ec2.sh
# Pode ser executado mais de uma vez com segurança.
set -euo pipefail

ARQUITETURA="$(uname -m)"
case "$ARQUITETURA" in
  x86_64) ARQ_BUILDX="amd64" ;;
  aarch64) ARQ_BUILDX="arm64" ;;
  *) echo "Arquitetura não suportada: $ARQUITETURA"; exit 1 ;;
esac

echo "==> Instalando Docker e Git..."
sudo dnf install -y docker git
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"

PLUGINS=/usr/local/lib/docker/cli-plugins
sudo mkdir -p "$PLUGINS"

if ! docker compose version >/dev/null 2>&1 && ! sudo docker compose version >/dev/null 2>&1; then
  echo "==> Instalando Docker Compose..."
  sudo curl -fsSL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-${ARQUITETURA}" \
    -o "$PLUGINS/docker-compose"
  sudo chmod +x "$PLUGINS/docker-compose"
fi

# O "docker compose build" exige o plugin buildx 0.17+. O pacote docker do
# Amazon Linux traz uma versão antiga (0.12), então checamos a versão, não só a presença.
buildx_atualizado() {
  local versao
  versao="$(sudo docker buildx version 2>/dev/null | grep -oE 'v?[0-9]+\.[0-9]+' | head -1 | tr -d v)" || return 1
  [ -n "$versao" ] && [ "$(printf '%s\n0.17\n' "$versao" | sort -V | head -1)" = "0.17" ]
}

if ! buildx_atualizado; then
  echo "==> Instalando Docker Buildx..."
  VERSAO_BUILDX="$(curl -fsSL https://api.github.com/repos/docker/buildx/releases/latest | grep -m1 '"tag_name"' | cut -d '"' -f4)"
  sudo curl -fsSL "https://github.com/docker/buildx/releases/download/${VERSAO_BUILDX}/buildx-${VERSAO_BUILDX}.linux-${ARQ_BUILDX}" \
    -o "$PLUGINS/docker-buildx"
  sudo chmod +x "$PLUGINS/docker-buildx"
fi

# t3.small tem 2 GB de RAM: o build do Angular junto com o MySQL pode estourar a memória.
if ! swapon --show | grep -q '/swapfile'; then
  echo "==> Criando 2 GB de swap..."
  sudo dd if=/dev/zero of=/swapfile bs=1M count=2048 status=none
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile >/dev/null
  sudo swapon /swapfile
  grep -q '^/swapfile' /etc/fstab || echo '/swapfile swap swap defaults 0 0' | sudo tee -a /etc/fstab >/dev/null
fi

echo
sudo docker --version
sudo docker compose version
sudo docker buildx version
free -h | grep -i -E 'mem|swap'
echo
echo "Pronto. Saia e entre novamente na sessão (exit) para usar 'docker' sem sudo."
