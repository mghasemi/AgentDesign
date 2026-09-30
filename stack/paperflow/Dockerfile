# PaperFlow with the OCR toolchain the profiles' ingestion skills expect.
# Identical to the Dockerfile running on the live host.
FROM ghcr.io/tylermorrison21/paperflow:latest

USER root

# System libraries required by OpenCV and PaddlePaddle
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Paddle, the advanced PaddleOCR pipelines, and a compatible urllib3
RUN pip install --no-cache-dir paddlepaddle "paddleocr[all]" "urllib3<2"
