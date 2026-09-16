FROM python:3.11-slim

# System deps needed by opencv / oemer
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Patch oemer: newer onnxruntime versions run a graph-optimization pass
# that's stricter about padding values than oemer's older exported model
# expects, causing "pads must not contain negative values" crashes.
# Disabling graph optimization for this session avoids the bad fusion
# pass entirely without needing to downgrade onnxruntime (which drags in
# incompatible numpy ABI issues).
RUN OEMER_PATH=$(python3 -c "import oemer, os; print(os.path.dirname(oemer.__file__))") && \
    sed -i \
      's/sess = rt.InferenceSession(onnx_path, providers=providers)/sess_options = rt.SessionOptions()\n        sess_options.graph_optimization_level = rt.GraphOptimizationLevel.ORT_DISABLE_ALL\n        sess = rt.InferenceSession(onnx_path, sess_options=sess_options, providers=providers)/' \
      "$OEMER_PATH/inference.py"

# Pre-download oemer's model weights at BUILD time, not at request time.
# This avoids the live web request timing out mid-download on slow/free
# hosting tiers, since oemer normally fetches these lazily on first use.
RUN OEMER_PATH=$(python3 -c "import oemer, os; print(os.path.dirname(oemer.__file__))") && \
    mkdir -p "$OEMER_PATH/checkpoints/unet_big" "$OEMER_PATH/checkpoints/seg_net" && \
    curl -L -o "$OEMER_PATH/checkpoints/unet_big/model.onnx" \
      https://github.com/BreezeWhite/oemer/releases/download/checkpoints/1st_model.onnx && \
    curl -L -o "$OEMER_PATH/checkpoints/unet_big/weights.h5" \
      https://github.com/BreezeWhite/oemer/releases/download/checkpoints/1st_weights.h5 && \
    curl -L -o "$OEMER_PATH/checkpoints/seg_net/model.onnx" \
      https://github.com/BreezeWhite/oemer/releases/download/checkpoints/2nd_model.onnx && \
    curl -L -o "$OEMER_PATH/checkpoints/seg_net/weights.h5" \
      https://github.com/BreezeWhite/oemer/releases/download/checkpoints/2nd_weights.h5

COPY backend/ backend/
COPY frontend/ frontend/

WORKDIR /app/backend

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
