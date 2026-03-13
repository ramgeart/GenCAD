<p align="center">
  <h1 align="center">GenCAD</h1>
  <h4 align="center">Image-conditioned Computer-Aided Design Generation with Transformer-based Contrastive Representation and Diffusion Priors</h4>
</p>

<p align="center">
  <a href="https://openreview.net/pdf?id=e817c1wEZ6">
    <img src="https://img.shields.io/badge/Paper-TMLR%202025-4b44ce.svg">
  </a>
  <a href="https://arxiv.org/abs/2409.16294">
    <img src="https://img.shields.io/badge/arXiv-2409.16294-b31b1b.svg">
  </a>
  <a href="https://gencad.github.io/">
    <img src="https://img.shields.io/badge/Project%20Page-Link-blue">
  </a>
</p>

---

<p align="center">
  <img src="assets/fig_10.png" alt="GenCAD Demo" width="700"/>
</p>

---

## 📁 Dataset 

Download from [here](https://drive.google.com/drive/folders/1M0dPr5kILGY9HTRCHox1vLLDhhxJWl_C?usp=sharing) and place it in the `data/` directory. 

---

## 📦 Pretrained Models

Download from [here](https://drive.google.com/drive/folders/1Ej7wdtlqT5P-SoUf3gsZXD8b78XqhiI5?usp=sharing) and place them in `data/ckpt/`.

---

## 🔧 Setup Options

First download the checkpoints and the dataset and put them in their respective directories. 

### Option 1: Docker (Recommended)

1. Clone the repo:
   ```bash
   git clone https://github.com/ferdous-alam/GenCAD
   cd GenCAD
   ```

2. Build the Docker image:
   ```bash
   docker build -t gencad:latest .
   ```

3. Run a script, for example training CSR:
   ```bash
   docker run -it gencad:latest conda run -n gencad_env python train_gencad.py csr -name test -gpu 0
   ```
4. For headless visualization (inference):

   First, enter the container with GPU access and mount the appropriate folders:

   ```bash
   docker run --gpus all \
     -v $(pwd)/data/images:/app/data/images \
     -v $(pwd)/assets:/app/assets \
     -v $(pwd)/results:/app/results \
     -it gencad:latest /bin/bash
   ```

   Then inside the container, run:

   ```bash
   xvfb-run --server-args="-screen 0 2048x2048x24" python inference_gencad.py -image_path data/images -export_img
   ```
---

### Option 2: Manual (conda + pip)


1. Create and activate a virtual environment with GPU support:
   ```bash
   conda create -n gencad_env python=3.10 -y
   conda activate gencad_env

2. Install `pythonocc-core` using conda:
   ```bash
   conda install -c conda-forge pythonocc-core=7.9.0
   ```

3. Install the rest via pip:
   ```bash
   pip install -r requirements.txt
   ```

4. Now run training or inference:
   ```bash
   python train_gencad.py csr -name test -gpu 0
   ```

---

## 🚀 Training

### CSR Model
```bash
python train_gencad.py csr -name test -gpu 0
```
Optional checkpoint:
```bash
python train_gencad.py csr -name test -gpu 0 -ckpt "model/ckpt/ae_ckpt_epoch1000.pth"
```

### CCIP Model
```bash
python train_gencad.py ccip -name test -gpu 0 -cad_ckpt "model/ckpt/ae_ckpt_epoch1000.pth"
```

### Diffusion Prior
```bash
python train_gencad.py dp -name test -gpu 0 -cad_emb 'data/embeddings/cad_embeddings.h5' -img_emb 'data/embeddings/sketch_embeddings.h5'
```

---

## 🧪 Inference

For headless systems (e.g. servers):

```bash
xvfb-run python inference_gencad.py
```

---

## 🖼 STL Visualization

Convert STL to PNG:
```bash
python stl2img.py -src path/to/stl/files -dst path/to/save/images
```

---

## 📊 Evaluation

Coming soon.

---

## 🖥️ UI – Interactive CAD Design

GenCAD ships with a browser-based UI that lets you design 3D models using a
2D/3D visual canvas and a chatbot area for natural-language commands.

### Features

- **3D Canvas** – interactive STL viewer with pan / zoom / rotate
- **Design chatbot** – type natural-language commands to create and modify shapes
- **Export** – download the current model as an STL file at any time

### Launch the UI

1. Make sure the environment is active (see *Setup Options* above).
2. Install the UI dependency:
   ```bash
   pip install "gradio>=4.0.0"
   ```
3. Start the server:
   ```bash
   python -m ui.app
   # or
   python ui/app.py
   ```
4. Open your browser at **http://localhost:7860**

### Supported commands

| Command | Example |
|---------|---------|
| `create box <w> <h> <d>` | `create box 20 10 5` |
| `create cylinder <r> <h>` | `create cylinder 5 20` |
| `create sphere <r>` | `create sphere 8` |
| `create cone <r1> <r2> <h>` | `create cone 10 0 25` |
| `create torus <R> <r>` | `create torus 15 4` |
| `export stl` | Export / download current model |
| `clear` | Remove the current shape |
| `help` | Full command reference |
