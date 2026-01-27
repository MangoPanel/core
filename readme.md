## Instalation

> [!NOTE]
> to run `./.venv/Scripts/activate.ps1` on windows, run in powershell `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`. This execution policy is local to given powershell terminal.

### Install via pip or uv pip:
Strongly recommend to make a virtual env using uv first:
```bash
uv venv
```
First install the PaddlePaddle package of your choice:
```bash
# CPU
uv pip install paddlepaddle==3.0.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/

# gpu，requires GPU driver version ≥450.80.02 (Linux) or ≥452.39 (Windows)
uv pip install paddlepaddle-gpu==3.0.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/

# gpu，requires GPU driver version ≥550.54.14 (Linux) or ≥550.54.14 (Windows)
uv pip install paddlepaddle-gpu==3.0.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu126/
```
Then you can use the automatic installation procedure based on pyproject.toml
```bash
uv pip install .
```

### contributing

Commit to your own branch.
```bash
git checkout -b first-name
```
or if the branch already exists
```bash
git checkout first-name
```

Once it's decided we're ready to merge, from main:
```bash
git merge first-name
```

After your repository was pushed, you're ready to update your branch to main
```bash
git pull origin main
```
