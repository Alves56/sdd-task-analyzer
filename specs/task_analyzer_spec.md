# Especificação SDD — TaskAnalyzer

Contrato técnico executável do módulo `src/task_analyzer.py`. Este arquivo é a
fonte de verdade do comportamento do sistema: o código e os testes devem seguir
exatamente o que está aqui, e qualquer mudança precisa ser versionada,
justificada e revisada.

| | |
|---|---|
| **Estudante** | Gabriel Bernardo Dias Alves |
| **Curso / Turma** | Ciência da Computação — Turma B |
| **Disciplina** | Bootcamp III |
| **Versão atual** | 1.2 |

## Histórico de versões

| Versão | Data | Origem | Resumo |
|---|---|---|---|
| 1.0 | 13/09/2026 | Fase 1 (Google Docs) | Especificação inicial, cenários de aceite e CONTEXT_RULES. |
| 1.1 | 17/10/2026 | Fase 2 (este repositório) | Alinhamento ao enunciado da Fase 2: métricas em horas, totais por status, exceção `TaskValidationError` e retorno 0.0 sem tarefas concluídas. Detalhes na seção 9. |
| 1.2 | 25/10/2026 | Fase 3 (este repositório) | Estrutura final do repositório e esteira de entrega: CI no GitHub Actions, Docker, `specs/system_design_document.pdf`, `specs/requirements.yaml` e branch `develop`. O contrato de negócio (seções 2 a 7) não muda. Detalhes nas seções 10 e 11. |

## 1. Propósito

O TaskAnalyzer analisa registros de execução de tarefas e gera métricas
objetivas de produtividade para apoiar a tomada de decisão:

- quantidade de tarefas por status, no geral e por prioridade;
- tempo médio de conclusão, no geral e por prioridade (baixa, média e alta);
- taxa de atraso: percentual de tarefas concluídas depois do prazo.

## 2. Interface pública

```python
def analyze_tasks(tasks: Sequence[Mapping[str, Any]]) -> ResultadoAnalise: ...

class TaskValidationError(ValueError): ...
```

- `analyze_tasks` recebe uma lista (ou tupla) de tarefas, cada uma um dicionário
  com os campos da seção 3, e devolve o dicionário descrito na seção 4.
- `TaskValidationError` é a exceção específica lançada quando a entrada viola o
  contrato (seção 6). A mensagem identifica a tarefa e o problema.
- A função não altera a entrada e não persiste dados em arquivos ou bancos.

## 3. Entradas

| Campo | Tipo | Obrigatório | Descrição / restrições |
|---|---|---|---|
| `id_tarefa` | `int` | Sim | Identificador único da tarefa, maior que 0. |
| `data_criacao` | `datetime` | Sim | Data e hora de criação. |
| `data_inicio` | `datetime` | Não | Data e hora de início da execução. |
| `data_conclusao` | `datetime` | Não* | Data e hora de conclusão. *Obrigatória quando `status` é `"concluída"`. |
| `prazo` | `datetime` | Sim | Data e hora limite para conclusão. |
| `prioridade` | `str` | Sim | Exatamente `"baixa"`, `"média"` ou `"alta"`. |
| `status` | `str` | Sim | Exatamente `"concluída"`, `"pendente"` ou `"cancelada"`. |

Fuso horário: todas as datas são tratadas em UTC. Datas sem fuso (naive) são
interpretadas como UTC; datas com outro fuso são convertidas para UTC.

## 4. Saídas

`analyze_tasks` devolve um dicionário com as métricas gerais e, em
`indicadores_por_prioridade`, as mesmas métricas para cada prioridade.

| Campo | Tipo | Descrição |
|---|---|---|
| `total_tarefas` | `int` | Total de tarefas recebidas (todos os status). |
| `total_concluidas` | `int` | Tarefas com status `"concluída"`. |
| `total_pendentes` | `int` | Tarefas com status `"pendente"`. |
| `total_canceladas` | `int` | Tarefas com status `"cancelada"`. |
| `tempo_medio_conclusao_horas` | `float` | Média, em horas, do tempo de conclusão das tarefas concluídas. |
| `taxa_atraso_percentual` | `float` | Percentual das tarefas concluídas que terminaram depois do prazo. |
| `indicadores_por_prioridade` | `dict` | Chaves `"baixa"`, `"média"` e `"alta"`, sempre presentes, cada uma com os seis campos acima (exceto este). |

Exemplo de saída:

```python
{
    "total_tarefas": 9,
    "total_concluidas": 6,
    "total_pendentes": 2,
    "total_canceladas": 1,
    "tempo_medio_conclusao_horas": 2.75,
    "taxa_atraso_percentual": 33.33,
    "indicadores_por_prioridade": {
        "baixa": {"total_tarefas": 2, "total_concluidas": 1, "total_pendentes": 1,
                  "total_canceladas": 0, "tempo_medio_conclusao_horas": 6.0,
                  "taxa_atraso_percentual": 0.0},
        "média": {...},
        "alta": {...},
    },
}
```

## 5. Regras de negócio

| Código | Regra |
|---|---|
| RN-01 | Apenas tarefas com status `"concluída"` entram no tempo médio e na taxa de atraso. Pendentes e canceladas entram só nas contagens. |
| RN-02 | Tempo de conclusão = `data_conclusao − data_inicio`. Se `data_inicio` não for informada, usa-se `data_criacao`. |
| RN-03 | O tempo de conclusão é expresso em horas. |
| RN-04 | Uma tarefa está atrasada quando `data_conclusao > prazo`. Concluir exatamente no prazo não é atraso. |
| RN-05 | Taxa de atraso = tarefas concluídas atrasadas ÷ tarefas concluídas × 100. |
| RN-06 | Sem tarefas concluídas (entrada vazia, só pendentes ou só canceladas), tempo médio e taxa de atraso valem `0.0`. A divisão por zero é evitada explicitamente, sem lançar exceção. |
| RN-07 | Tempos e percentuais são arredondados para duas casas decimais, com arredondamento "meio para cima" (ex.: 1,125 → 1,13). |
| RN-08 | Todas as datas são tratadas em UTC (seção 3). |
| RN-09 | As três prioridades aparecem sempre em `indicadores_por_prioridade`, mesmo sem tarefas (valores zerados). |

## 6. Validações (lançam `TaskValidationError`)

| Código | Situação inválida |
|---|---|
| VAL-01 | A entrada não é uma lista ou tupla de tarefas, ou um item não é um dicionário. |
| VAL-02 | Campo obrigatório ausente ou `None`. |
| VAL-03 | `id_tarefa` não é inteiro, é menor ou igual a 0, ou se repete. |
| VAL-04 | Campo de data com valor que não é `datetime`. |
| VAL-05 | `prioridade` ou `status` fora dos valores permitidos. |
| VAL-06 | Datas inconsistentes: `data_conclusao` anterior a `data_criacao`, `data_conclusao` anterior a `data_inicio` ou `data_inicio` anterior a `data_criacao`. |
| VAL-07 | Tarefa com status `"concluída"` sem `data_conclusao`. |

## 7. Cenários de aceite (Dado — Quando — Então)

### Cenário 1 — Sucesso: métricas corretas

- **Dado** um conjunto de tarefas válidas, com diferentes prioridades, prazos e
  status, contendo registros concluídos com datas consistentes;
- **Quando** o analisador de tarefas for executado;
- **Então** o sistema deve retornar `total_tarefas`, `total_concluidas` e
  `total_pendentes` corretos, o tempo médio de conclusão em horas (geral e por
  prioridade) e a taxa de atraso correta (geral e por prioridade).

### Cenário 2 — Exceção/erro: entradas inválidas

- **Dado** uma entrada com datas inconsistentes, por exemplo `data_conclusao`
  anterior a `data_criacao` (ou ao início), ou com dados fora do contrato;
- **Quando** o analisador de tarefas for executado;
- **Então** o sistema deve lançar `TaskValidationError` com mensagem clara e
  objetiva, sem comportamento indefinido.

### Casos de borda — ausência de tarefas concluídas

- **Dado** uma entrada vazia, ou apenas com tarefas pendentes ou canceladas;
- **Quando** o analisador de tarefas for executado;
- **Então** o sistema deve retornar `0.0` para o tempo médio e a taxa de atraso,
  com as contagens corretas, sem lançar exceções.

## 8. Rastreabilidade (cenário → teste)

| Cenário / regra | Testes em `tests/test_harness.py` |
|---|---|
| Cenário 1 (RN-01 a RN-05, RN-07, RN-09) | `test_cenario1_*` |
| Cenário 2 (VAL-01 a VAL-07) | `test_cenario2_*` |
| Casos de borda (RN-06, RN-08) | `test_borda_*` |

## 9. Mudanças da versão 1.0 para a 1.1 (justificativas)

A versão 1.0 foi escrita na Fase 1. O enunciado da Fase 2 definiu de forma
explícita os campos e comportamentos que o Test Harness deve validar, e alguns
pontos da 1.0 estavam em conflito com ele ou entre si. Em vez de deixar a IA
escolher sozinha, as mudanças foram decididas na revisão humana e registradas
aqui:

1. **Tempo em horas.** `tempo_medio_conclusao_min` (minutos) passou a
   `tempo_medio_conclusao_horas`, nome e unidade exigidos no enunciado da Fase 2.
2. **Totais por status.** `quantidade_tarefas` foi detalhado em
   `total_tarefas`, `total_concluidas`, `total_pendentes` e `total_canceladas`,
   no geral e por prioridade.
3. **Datas inconsistentes geram exceção.** A 1.0 dizia "ignorar tarefas com
   datas inconsistentes" (regra) e "gerar exceção específica" (Cenário 2). A 1.1
   mantém o Cenário 2: a entrada é rejeitada com `TaskValidationError`, para não
   esconder erros de dados.
4. **Sem tarefas concluídas, 0.0.** A 1.0 previa exceção quando não houvesse
   tarefas concluídas. O enunciado da Fase 2 exige retorno 0.0 sem exceção, então
   a divisão por zero agora é tratada devolvendo 0.0 (RN-06).
5. **`data_inicio` ausente.** A 1.0 não dizia o que fazer quando uma tarefa
   concluída não tem `data_inicio`. A 1.1 define que se usa `data_criacao`
   (RN-02), para que a IA não precise supor um comportamento.
6. **Detalhes explícitos.** Concluir exatamente no prazo não é atraso (RN-04),
   arredondamento meio para cima (RN-07) e datas sem fuso interpretadas como UTC
   (seção 3).

## 10. Estrutura do repositório e esteira de entrega (v1.2)

A seção 4.1 do documento da Fase 1 definiu a árvore do repositório, e o
`CONTEXT_RULES.md` proíbe modificá-la. O enunciado da Fase 3 exige arquivos e
pastas novos. A inclusão abaixo foi autorizada pelo humano responsável e é
registrada aqui como nova versão, em vez de ser feita pela IA por conta própria.

```
sdd-task-analyzer/
├── .github/
│   └── workflows/
│       └── ci.yml                    # CI: pytest a cada push e pull request
├── Dockerfile                        # Imagem python:3.11-slim que roda o pytest
├── docker-compose.yml                # Serviço que roda a suíte com um comando
├── CONTEXT_RULES.md                  # Regras de governança para a IA
├── specs/
│   ├── task_analyzer_spec.md         # Este contrato (versão vigente)
│   ├── system_design_document.pdf   # Documento SDD em PDF
│   └── requirements.yaml             # Requisitos e regras em formato de máquina
├── tests/
│   └── test_harness.py               # Test Harness (inalterado desde a Fase 2)
├── src/
│   └── task_analyzer.py              # Código gerado via IA e homologado
├── .gitignore
├── .dockerignore                     # Arquivos que não entram na imagem Docker
├── requirements.txt                  # Dependência autorizada: pytest
└── README.md
```

Esteira de entrega:

| Etapa | Ferramenta | Regra |
|---|---|---|
| Integração contínua | GitHub Actions (`ubuntu-latest`, Python 3.11) | Roda `pytest tests/test_harness.py -v` em todo push e pull request para `main` e `develop`. O merge só acontece com o build verde. |
| Portabilidade | Docker (`python:3.11-slim`) e Docker Compose | A mesma suíte roda dentro de um container isolado, com um único comando. |
| Fluxo Git | `feature/*` → `develop` → `main` | Cada tema chega à `develop` por Pull Request homologado; a `develop` chega à `main` por Pull Request. |

## 11. Mudanças da versão 1.1 para a 1.2 (justificativas)

1. **Arquivos de infraestrutura.** `.github/workflows/ci.yml`, `Dockerfile`,
   `docker-compose.yml` e `.dockerignore` passam a fazer parte da estrutura,
   porque o enunciado da Fase 3 exige CI e containerização. Eles não são
   bibliotecas do código de produção: o `src/` continua só com a biblioteca
   padrão, e a única dependência instalada é o `pytest`.
2. **Documentos de especificação.** `specs/system_design_document.pdf` (o
   documento SDD da Fase 1 em PDF, com um adendo das versões 1.1 e 1.2) e
   `specs/requirements.yaml` (requisitos, regras e validações em formato
   legível por máquina) foram acrescentados. Este arquivo continua sendo o
   contrato vigente.
3. **Branch `develop`.** A estratégia de versionamento da Fase 1 (seção 4.3)
   previa `main`, `develop` e `feature/*`; na Fase 2 a `develop` não foi usada.
   A partir da 1.2 ela passa a ser a branch de integração.
4. **Contrato inalterado.** Entradas, saídas, regras de negócio (RN-01 a
   RN-09), validações (VAL-01 a VAL-07) e cenários de aceite continuam iguais
   aos da versão 1.1. O `tests/test_harness.py` e o `src/task_analyzer.py` não
   são modificados nesta versão.
