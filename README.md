# sdd-task-analyzer

O **TaskAnalyzer** analisa registros de tarefas e calcula métricas de
produtividade: totais por status, tempo médio de conclusão em horas e taxa de
atraso, no geral e por prioridade (baixa, média e alta).

Projeto do Bootcamp III (Ciência da Computação), desenvolvido com
**Spec-Driven Development (SDD)**: a especificação é a fonte de verdade, o
código é gerado por assistente de IA guiado pelas regras de contexto e só chega
à `main` depois da homologação humana, com testes automatizados.

**Status:** Fase 2 concluída. Test Harness com pytest: 100% dos testes
aprovados (`python -m pytest -v`).

## Estrutura

```
sdd-task-analyzer/
├── README.md                    # Este arquivo
├── CONTEXT_RULES.md             # Regras de governança para a IA
├── .gitignore                   # Arquivos ignorados pelo Git
├── requirements.txt             # Dependência autorizada: pytest
├── specs/
│   └── task_analyzer_spec.md    # Contrato SDD (versão 1.1)
├── tests/
│   └── test_harness.py          # Test Harness: Cenários 1 e 2 e casos de borda
└── src/
    └── task_analyzer.py         # Código gerado via IA e homologado
```

## Como executar os testes

Requisito: Python 3.11 ou superior.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m pytest -v
```

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
3. Todo código passou pelo checklist de homologação do `CONTEXT_RULES.md`
   antes do merge, registrado nos Pull Requests.

## Fluxo Git

| Branch | Conteúdo |
|---|---|
| `main` | Versão homologada |
| `feature/sdd-specification` | Especificação SDD, CONTEXT_RULES e dependências |
| `feature/test-harness` | Test Harness com pytest |
| `feature/task-analyzer-impl` | Implementação gerada via IA e README |

As branches chegam à `main` por Pull Requests documentados. A entrega da
Fase 2 está marcada com a tag `v0.2.0`.

## Autor

Gabriel Bernardo Dias Alves, Ciência da Computação, Turma B.
