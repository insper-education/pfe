# Instrucoes Para Agentes

Este projeto deve ser executado no ambiente Conda `pfe`.

- Para comandos Python/Django, use `conda run -n pfe ...`.
- Nao use o Python do sistema base nem o stub do WindowsApps.
- Em shells nao interativos, prefira `conda run -n pfe` em vez de `conda activate pfe`.

Exemplos:

```powershell
conda run -n pfe python manage.py check
conda run -n pfe python manage.py test
conda run -n pfe python manage.py runserver
```

Se for necessario abrir um shell interativo manualmente, ative antes:

```powershell
conda activate pfe
```
