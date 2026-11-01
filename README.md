
### Verificación opcional de la GPU (RTX 5060)

Si has sincronizado el grupo **cuda** (ver paso 0) puedes comprobar que Python reconoce la GPU con el siguiente comando:

```bash
uv run python - <<'PY'
import torch
print('CUDA disponible:', torch.cuda.is_available())
if torch.cuda.is_available():
    print('GPU detectada:', torch.cuda.get_device_name(0))
PY
```

En caso de que `torch` no esté instalado, ejecuta nuevamente:

```bash
uv sync --group cuda
```

Este comando no es necesario para la ejecución del parcial (el algoritmo usa solo CPU), pero permite validar que el entorno reconoce tu RTX 5060 y que, si en un futuro decides usar aceleración CUDA, la configuración ya está lista.
