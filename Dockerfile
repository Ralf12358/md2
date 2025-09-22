FROM node:22.11.0-bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=false \
    NODE_PATH=/app/node_modules \
    PUPPETEER_CACHE_DIR=/opt/puppeteer

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    wget \
    git \
    python3 \
    python3-pip \
    fonts-dejavu-core fonts-dejavu-extra fonts-liberation \
    librsvg2-bin \
    libc6 \
    libgtk-3-0 \
    libx11-6 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libasound2 \
    libpangocairo-1.0-0 \
    libnspr4 \
    libnss3 \
    libxss1 \
    libgconf-2-4 \
    libxkbcommon0 \
    libgbm1 \
    && rm -rf /var/lib/apt/lists/*

ARG PANDOC_VERSION=3.8
RUN ARCH=$(dpkg --print-architecture) \
    && case "$ARCH" in \
    amd64) PANDOC_ARCH=amd64 ;; \
    arm64) PANDOC_ARCH=arm64 ;; \
    *) echo "unsupported arch: $ARCH" && exit 1 ;; \
    esac \
    && echo "Downloading pandoc ${PANDOC_VERSION} for $PANDOC_ARCH..." \
    && curl -L --http1.1 --progress-bar -o /tmp/pandoc.deb \
    "https://github.com/jgm/pandoc/releases/download/${PANDOC_VERSION}/pandoc-${PANDOC_VERSION}-1-${PANDOC_ARCH}.deb" \
    && ls -lh /tmp/pandoc.deb \
    && dpkg -i /tmp/pandoc.deb \
    && rm -f /tmp/pandoc.deb

RUN npm install -g @mermaid-js/mermaid-cli@11.10.1

ENV PUPPETEER_ARGS="--no-sandbox --disable-setuid-sandbox --disable-dev-shm-usage --disable-gpu"

# Pin python filter tools
RUN pip3 install --break-system-packages pandoc-mermaid-filter==0.1.0 pandocfilters==1.5.1 PyMuPDF==1.24.12

# Provide MathJax locally to avoid network inside container
RUN mkdir -p /mathjax && \
    wget -q -O /tmp/mathjax.tgz https://registry.npmmirror.com/mathjax/-/mathjax-3.2.2.tgz && \
    tar -xzf /tmp/mathjax.tgz -C /tmp && \
    cp -r /tmp/package/es5 /mathjax && \
    mv /mathjax/es5/tex-svg-full.js /mathjax/tex-svg-full.js && \
    rm -rf /tmp/package /tmp/mathjax.tgz

RUN printf '{\n  "args": ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]\n}\n' > /usr/local/bin/puppeteer.json

WORKDIR /app
COPY src/md2/scripts/package.json /app/package.json
RUN npm install --omit=dev && \
    chmod -R a+rx /opt/puppeteer || true
RUN printf '#!/usr/bin/env bash\nexec mmdc "$@"\n' > /usr/local/bin/mermaid && chmod +x /usr/local/bin/mermaid
COPY src/md2/scripts/print.js /app/print.js

WORKDIR /work
