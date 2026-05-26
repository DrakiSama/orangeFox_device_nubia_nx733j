#!/bin/bash
# Instalar dependencias de build para OrangeFox Recovery
# Ejecutar en WSL Ubuntu 24.04

set -e

echo "[*] Instalando dependencias de build Android/OFRP..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
    android-sdk-libsparse-utils \
    android-sdk-ext4-utils \
    adb fastboot \
    autoconf automake bc bison build-essential \
    ccache clang cmake curl \
    flex g++ gawk gcc gettext git gnupg gperf \
    imagemagick jq \
    libarchive-tools libbz2-dev libelf-dev liblz4-tool \
    libncurses5 libncurses-dev libsdl1.2-dev libssl-dev \
    libxml2 libxml2-utils lz4 lzop \
    m4 make ·multilib \
    ninja-build \
    openjdk-17-jdk openjdk-17-jre \
    patchelf \
    pkg-config \
    python3 python3-pip python3-venv \
    rsync \
    schedtool \
    screen \
    squashfs-tools \
    sudo \
    texinfo \
    timeshift \
    tmate \
    tree \
    tzdata \
    unzip \
    uuid-dev \
    wget \
    xz-utils \
    zip \
    zlib1g-dev \
    zram-tools

# Configurar ccache
echo "[*] Configurando ccache..."
echo 'export USE_CCACHE=1' >> ~/.bashrc
echo 'export CCACHE_DIR=~/.ccache' >> ~/.bashrc
echo 'export CCACHE_MAXSIZE=10G' >> ~/.bashrc
ccache --set-config=max_size=10G
ccache --set-config=compression=true

# Repo tool
echo "[*] Instalando repo..."
if ! command -v repo &>/dev/null; then
    sudo curl -sS https://storage.googleapis.com/git-repo-downloads/repo -o /usr/local/bin/repo
    sudo chmod a+x /usr/local/bin/repo
fi

# Git config
git config --global user.name "Draki"
git config --global user.email "draki@users.noreply.github.com"

echo ""
echo "[✔] Build dependencies installed."
echo "    Espacio en disco:"
df -h /
