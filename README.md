# sdd-task-analyzer

[![CI](https://github.com/Alves56/sdd-task-analyzer/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Alves56/sdd-task-analyzer/actions/workflows/ci.yml)

O **TaskAnalyzer** analisa registros de tarefas e calcula métricas de
produtividade: totais por status, tempo médio de conclusão em horas e taxa de
atraso, no geral e por prioridade (baixa, média e alta).

Projeto do Bootcamp III (Ciência da Computação), desenvolvido com
**Spec-Driven Development (SDD)**: a especificação é a fonte de verdade, o
código é gerado por assistente de IA guiado pelas regras de contexto e só chega
à `main` depois da homologação humana, com testes automatizados.

**Status:** Fase 3 (entrega final) concluída. Os 43 testes do Test Harness
passam em três lugares: na máquina local, no GitHub Actions a cada push e pull
request, e dentro de um container Docker (`python:3.11-slim`).

## Estrutura

```
sdd-task-analyzer/
├── .github/
│   └── workflows/
│       └── ci.yml                    # CI: testes + Docker a cada push e PR
├── Dockerfile                        # Imagem python:3.11-slim que roda o pytest
├── docker-compose.yml                # Serviço "testes": a suíte com um comando
├── CONTEXT_RULES.md                  # Regras de governança para a IA (v1.2)
├── specs/
│   ├── task_analyzer_spec.md         # Contrato SDD vigente (v1.2)
│   ├── system_design_document.pdf    # SDD da Fase 1 + adendo v1.1 e v1.2
│   └── requirements.yaml             # Requisitos em formato de máquina
├── tests/
│   └── test_harness.py               # Test Harness: Cenários 1 e 2 e casos de borda
├── src/
│   └── task_analyzer.py              # Código gerado via IA e homologado
├── .gitignore / .dockerignore        # Arquivos fora do Git / fora da imagem
├── requirements.txt                  # Dependência autorizada: pytest
└── README.md                         # Este arquivo
```

## Como executar os testes

### Localmente

Requisito: Python 3.11 ou superior.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m pytest -v
```

### Com Docker

Requisito: Docker (no Windows, o Docker Desktop). Não precisa ter Python
instalado: a imagem já traz o Python 3.11 e o pytest.

```bash
docker build -t sdd-task-analyzer .
docker run --rm sdd-task-analyzer
```

Ou, com um único comando (o Compose constrói a imagem se ela não existir):

```bash
docker compose run --rm testes
```

O `Dockerfile` parte de `python:3.11-slim`, instala o `requirements.txt`,
copia o código e define `pytest tests/test_harness.py -v` como comando
principal (`CMD`). O `--rm` apaga o container ao terminar.

### No GitHub Actions (CI)

O workflow [`.github/workflows/ci.yml`](.github/workflows/ci.yml) roda a cada
push ou pull request nas branches `main` e `develop`, em `ubuntu-latest` com
Python 3.11:

1. **Testes (pytest, Python 3.11):** instala o `requirements.txt` e executa
   `pytest tests/test_harness.py -v`.
2. **Docker (build e testes no container):** depois do job anterior, roda
   `docker build`, `docker run` e `docker compose run`, provando que a suíte
   passa fora da máquina do desenvolvedor.

O histórico das execuções fica na aba
[Actions](https://github.com/Alves56/sdd-task-analyzer/actions/workflows/ci.yml).

## Exemplo de uso

Na raiz do repositório, com `src` no caminho de importação
(`PYTHONPATH=src python`; no PowerShell: `$env:PYTHONPATH="src"; python`):

```python
from datetime import UTC, datetime

from task_analyzer import analyze_tasks

tarefas = [
    {
        "id_tarefa": 1,
        "data_criacao": datetime(2026, 9, 1, 8, tzinfo=UTC),
        "data_inicio": datetime(2026, 9, 1, 9, tzinfo=UTC),
        "data_conclusao": datetime(2026, 9, 1, 11, tzinfo=UTC),
        "prazo": datetime(2026, 9, 1, 12, tzinfo=UTC),
        "prioridade": "alta",
        "status": "concluída",
    },
    {
        "id_tarefa": 2,
        "data_criacao": datetime(2026, 9, 1, 8, tzinfo=UTC),
        "data_inicio": datetime(2026, 9, 1, 10, tzinfo=UTC),
        "data_conclusao": datetime(2026, 9, 1, 14, tzinfo=UTC),
        "prazo": datetime(2026, 9, 1, 13, tzinfo=UTC),
        "prioridade": "baixa",
        "status": "concluída",
    },
    {
        "id_tarefa": 3,
        "data_criacao": datetime(2026, 9, 1, 8, tzinfo=UTC),
        "prazo": datetime(2026, 9, 2, 18, tzinfo=UTC),
        "prioridade": "média",
        "status": "pendente",
    },
]

resultado = analyze_tasks(tarefas)
```

Métricas gerais do exemplo (o resultado traz também
`indicadores_por_prioridade`, com as mesmas métricas para cada prioridade):

```python
{
    "total_tarefas": 3,
    "total_concluidas": 2,
    "total_pendentes": 1,
    "total_canceladas": 0,
    "tempo_medio_conclusao_horas": 3.0,
    "taxa_atraso_percentual": 50.0,
}
```

Entradas fora do contrato, como `data_conclusao` anterior a `data_criacao`,
lançam `TaskValidationError` com uma mensagem que identifica a tarefa.

## Contrato

- Função pública: `analyze_tasks(tasks)`. Exceção: `TaskValidationError`.
- Entradas, saídas, regras de negócio (RN-01 a RN-09), validações (VAL-01 a
  VAL-07) e cenários de aceite: [`specs/task_analyzer_spec.md`](specs/task_analyzer_spec.md).
- Regras para a IA e checklist de homologação: [`CONTEXT_RULES.md`](CONTEXT_RULES.md).

## Desenvolvimento assistido por IA

1. O assistente de IA recebeu o `CONTEXT_RULES.md` e a especificação antes de
   gerar qualquer código.
2. Conflitos entre a especificação da Fase 1 e o enunciado da Fase 2 foram
   decididos na revisão humana e registrados como versão 1.1 da especificação
   (seção 9), em vez de deixar a IA supor um comportamento.
3. Na Fase 3, a inclusão dos arquivos de CI, Docker e specs (proibida pelas
   regras sem autorização) foi autorizada pelo autor e registrada como versão
   1.2 da especificação e do `CONTEXT_RULES.md`, antes de qualquer arquivo novo.
4. Todo código passou pelo checklist de homologação do `CONTEXT_RULES.md`
   antes do merge, com CI verde e registro nos Pull Requests.

## Fluxo Git

| Branch | Conteúdo |
|---|---|
| `main` | Versão homologada |
| `develop` | Integração das funcionalidades da Fase 3 |
| `feature/sdd-specification` | Especificação SDD, CONTEXT_RULES e dependências (Fase 2) |
| `feature/test-harness` | Test Harness com pytest (Fase 2) |
| `feature/task-analyzer-impl` | Implementação gerada via IA e README (Fase 2) |
| `feature/governanca-v1.2` | Especificação e CONTEXT_RULES v1.2 (Fase 3) |
| `feature/ci-github-actions` | Workflow do GitHub Actions (Fase 3) |
| `feature/docker` | Dockerfile, docker-compose e job Docker no CI (Fase 3) |
| `feature/specs-finais` | `system_design_document.pdf` e `requirements.yaml` (Fase 3) |
| `feature/docs-fase3` | Este README (Fase 3) |

Na Fase 3 o fluxo é `feature/*` → `develop` → `main`, sempre por Pull Request
com CI verde e homologação humana. Tags: `v0.2.0` (Fase 2) e `v1.0.0`
(entrega final).

## Links da entrega

| Item | Link |
|---|---|
| Repositório | https://github.com/Alves56/sdd-task-analyzer |
| Execuções do CI | https://github.com/Alves56/sdd-task-analyzer/actions/workflows/ci.yml |
| Pull Requests | https://github.com/Alves56/sdd-task-analyzer/pulls?q=is%3Apr |
| Especificação da Fase 1 (Google Docs) | https://docs.google.com/document/d/1lSOOjTPJeJQ6uU3M9VIdqoJWZwYZb8lpW3t8AdRD8mI/edit |
| Vídeo da Fase 1 | https://youtu.be/6MV0MZCqcXs |
| Vídeo da Fase 2 | https://youtu.be/lCYGY6-NILs |

## Autor

Gabriel Bernardo Dias Alves, Ciência da Computação, Turma B.
