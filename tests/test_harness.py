"""Test Harness do TaskAnalyzer (pytest).

Traduz em testes automatizados os cenários de aceite de
``specs/task_analyzer_spec.md`` (seções 7 e 8):

- Cenário 1, sucesso com métricas corretas: ``test_cenario1_*``.
- Cenário 2, exceção para entradas inválidas: ``test_cenario2_*``.
- Casos de borda, sem tarefas concluídas e fuso horário: ``test_borda_*``.

Execução, na raiz do repositório: ``python -m pytest -v``.
"""

import copy
import sys
from collections.abc import Callable
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

# Permite importar src/task_analyzer.py sem alterar a estrutura de pastas.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from task_analyzer import TaskValidationError, analyze_tasks  # noqa: E402

FabricaDeTarefa = Callable[..., dict[str, Any]]

METRICAS_ZERADAS: dict[str, Any] = {
    "total_tarefas": 0,
    "total_concluidas": 0,
    "total_pendentes": 0,
    "total_canceladas": 0,
    "tempo_medio_conclusao_horas": 0.0,
    "taxa_atraso_percentual": 0.0,
}


def utc(dia: int, hora: int, minuto: int = 0) -> datetime:
    """Cria uma data de setembro de 2026 no fuso UTC.

    Args:
        dia: Dia do mês.
        hora: Hora do dia.
        minuto: Minuto da hora.

    Returns:
        A data correspondente, em UTC.
    """
    return datetime(2026, 9, dia, hora, minuto, tzinfo=UTC)


@pytest.fixture
def nova_tarefa() -> FabricaDeTarefa:
    """Fábrica de tarefas válidas; os argumentos substituem os campos padrão.

    Returns:
        Função que cria uma tarefa concluída de prioridade alta, com 2 horas
        de execução e concluída antes do prazo.
    """

    def fabricar(**campos: Any) -> dict[str, Any]:
        tarefa: dict[str, Any] = {
            "id_tarefa": 1,
            "data_criacao": utc(1, 8),
            "data_inicio": utc(1, 9),
            "data_conclusao": utc(1, 11),
            "prazo": utc(1, 12),
            "prioridade": "alta",
            "status": "concluída",
        }
        tarefa.update(campos)
        return tarefa

    return fabricar


@pytest.fixture
def tarefas_cenario1(nova_tarefa: FabricaDeTarefa) -> list[dict[str, Any]]:
    """Massa de dados do Cenário 1: prioridades, prazos e status variados.

    Returns:
        Nove tarefas válidas. Seis concluídas (duas com atraso), duas
        pendentes e uma cancelada.
    """
    return [
        # Alta: 2 h no prazo, 4 h com atraso e 1 pendente.
        nova_tarefa(id_tarefa=1),
        nova_tarefa(
            id_tarefa=2,
            data_inicio=utc(1, 10),
            data_conclusao=utc(1, 14),
            prazo=utc(1, 13),
        ),
        nova_tarefa(
            id_tarefa=3,
            data_conclusao=None,
            prazo=utc(1, 18),
            status="pendente",
        ),
        # Média: 1 h no prazo, 3 h com atraso (sem data_inicio, conta desde a
        # criação), 0,5 h no prazo e 1 cancelada.
        nova_tarefa(
            id_tarefa=4,
            data_inicio=utc(1, 8, 30),
            data_conclusao=utc(1, 9, 30),
            prazo=utc(1, 10),
            prioridade="média",
        ),
        nova_tarefa(
            id_tarefa=5,
            data_inicio=None,
            data_conclusao=utc(1, 11),
            prazo=utc(1, 10),
            prioridade="média",
        ),
        nova_tarefa(
            id_tarefa=6,
            data_inicio=None,
            data_conclusao=None,
            prioridade="média",
            status="cancelada",
        ),
        nova_tarefa(
            id_tarefa=9,
            data_inicio=utc(1, 12),
            data_conclusao=utc(1, 12, 30),
            prazo=utc(1, 13),
            prioridade="média",
        ),
        # Baixa: 6 h no prazo e 1 pendente.
        nova_tarefa(
            id_tarefa=7,
            data_conclusao=utc(1, 15),
            prazo=utc(2, 8),
            prioridade="baixa",
        ),
        nova_tarefa(
            id_tarefa=8,
            data_inicio=None,
            data_conclusao=None,
            prazo=utc(3, 8),
            prioridade="baixa",
            status="pendente",
        ),
    ]


# ---------------------------------------------------------------------------
# Cenário 1 — Sucesso: métricas corretas
# ---------------------------------------------------------------------------


def test_cenario1_totais_gerais(
    tarefas_cenario1: list[dict[str, Any]],
) -> None:
    """Conta total, concluídas, pendentes e canceladas (RN-01)."""
    resultado = analyze_tasks(tarefas_cenario1)

    assert resultado["total_tarefas"] == 9
    assert resultado["total_concluidas"] == 6
    assert resultado["total_pendentes"] == 2
    assert resultado["total_canceladas"] == 1


def test_cenario1_tempo_medio_geral_em_horas(
    tarefas_cenario1: list[dict[str, Any]],
) -> None:
    """Tempo médio geral: (2 + 4 + 1 + 3 + 0,5 + 6) / 6 = 2,75 h (RN-02/03)."""
    resultado = analyze_tasks(tarefas_cenario1)

    assert resultado["tempo_medio_conclusao_horas"] == 2.75


def test_cenario1_taxa_atraso_geral(
    tarefas_cenario1: list[dict[str, Any]],
) -> None:
    """Duas atrasadas entre seis concluídas: 33,33% (RN-04, RN-05, RN-07)."""
    resultado = analyze_tasks(tarefas_cenario1)

    assert resultado["taxa_atraso_percentual"] == 33.33


@pytest.mark.parametrize(
    ("prioridade", "esperado"),
    [
        (
            "alta",
            {
                "total_tarefas": 3,
                "total_concluidas": 2,
                "total_pendentes": 1,
                "total_canceladas": 0,
                "tempo_medio_conclusao_horas": 3.0,
                "taxa_atraso_percentual": 50.0,
            },
        ),
        (
            "média",
            {
                "total_tarefas": 4,
                "total_concluidas": 3,
                "total_pendentes": 0,
                "total_canceladas": 1,
                "tempo_medio_conclusao_horas": 1.5,
                "taxa_atraso_percentual": 33.33,
            },
        ),
        (
            "baixa",
            {
                "total_tarefas": 2,
                "total_concluidas": 1,
                "total_pendentes": 1,
                "total_canceladas": 0,
                "tempo_medio_conclusao_horas": 6.0,
                "taxa_atraso_percentual": 0.0,
            },
        ),
    ],
)
def test_cenario1_metricas_por_prioridade(
    tarefas_cenario1: list[dict[str, Any]],
    prioridade: str,
    esperado: dict[str, Any],
) -> None:
    """Calcula todas as métricas para cada prioridade (RN-09)."""
    resultado = analyze_tasks(tarefas_cenario1)

    assert resultado["indicadores_por_prioridade"][prioridade] == esperado


def test_cenario1_sem_data_inicio_conta_desde_a_criacao(
    nova_tarefa: FabricaDeTarefa,
) -> None:
    """Sem data_inicio, o tempo é contado a partir da criação (RN-02)."""
    tarefa = nova_tarefa(data_inicio=None, data_conclusao=utc(1, 13))

    resultado = analyze_tasks([tarefa])

    assert resultado["tempo_medio_conclusao_horas"] == 5.0


def test_cenario1_conclusao_exatamente_no_prazo_nao_e_atraso(
    nova_tarefa: FabricaDeTarefa,
) -> None:
    """Concluir exatamente no prazo não conta como atraso (RN-04)."""
    tarefa = nova_tarefa(data_conclusao=utc(1, 12), prazo=utc(1, 12))

    resultado = analyze_tasks([tarefa])

    assert resultado["taxa_atraso_percentual"] == 0.0


def test_cenario1_arredonda_duas_casas_meio_para_cima(
    nova_tarefa: FabricaDeTarefa,
) -> None:
    """Média de 1 h e 1,25 h = 1,125 h, arredondada para 1,13 (RN-07)."""
    tarefas = [
        nova_tarefa(id_tarefa=1, data_conclusao=utc(1, 10)),
        nova_tarefa(id_tarefa=2, data_conclusao=utc(1, 10, 15)),
    ]

    resultado = analyze_tasks(tarefas)

    assert resultado["tempo_medio_conclusao_horas"] == 1.13


def test_cenario1_tipos_do_resultado(
    tarefas_cenario1: list[dict[str, Any]],
) -> None:
    """Contagens são int e métricas são float, no geral e por prioridade."""
    resultado = analyze_tasks(tarefas_cenario1)
    grupos = [resultado, *resultado["indicadores_por_prioridade"].values()]

    for grupo in grupos:
        assert type(grupo["total_tarefas"]) is int
        assert type(grupo["total_concluidas"]) is int
        assert type(grupo["total_pendentes"]) is int
        assert type(grupo["tempo_medio_conclusao_horas"]) is float
        assert type(grupo["taxa_atraso_percentual"]) is float


def test_cenario1_nao_altera_a_entrada(
    tarefas_cenario1: list[dict[str, Any]],
) -> None:
    """A análise não modifica os dados recebidos."""
    copia = copy.deepcopy(tarefas_cenario1)

    analyze_tasks(tarefas_cenario1)

    assert tarefas_cenario1 == copia


# ---------------------------------------------------------------------------
# Cenário 2 — Exceção/erro: entradas inválidas
# ---------------------------------------------------------------------------


def test_cenario2_conclusao_anterior_a_criacao(
    nova_tarefa: FabricaDeTarefa,
) -> None:
    """data_conclusao < data_criacao dispara TaskValidationError (VAL-06)."""
    tarefa = nova_tarefa(
        id_tarefa=7,
        data_inicio=None,
        data_criacao=utc(1, 10),
        data_conclusao=utc(1, 9),
    )

    with pytest.raises(
        TaskValidationError,
        match=r"Tarefa 7: .*data_conclusao .* é anterior a data_criacao",
    ):
        analyze_tasks([tarefa])


def test_cenario2_conclusao_anterior_ao_inicio(
    nova_tarefa: FabricaDeTarefa,
) -> None:
    """data_conclusao < data_inicio dispara TaskValidationError (VAL-06)."""
    tarefa = nova_tarefa(data_inicio=utc(1, 12), data_conclusao=utc(1, 11))

    with pytest.raises(
        TaskValidationError,
        match=r"data_conclusao .* é anterior a data_inicio",
    ):
        analyze_tasks([tarefa])


def test_cenario2_inicio_anterior_a_criacao(
    nova_tarefa: FabricaDeTarefa,
) -> None:
    """data_inicio < data_criacao dispara TaskValidationError (VAL-06)."""
    tarefa = nova_tarefa(data_inicio=utc(1, 7))

    with pytest.raises(
        TaskValidationError,
        match=r"data_inicio .* é anterior a data_criacao",
    ):
        analyze_tasks([tarefa])


def test_cenario2_concluida_sem_data_conclusao(
    nova_tarefa: FabricaDeTarefa,
) -> None:
    """Tarefa concluída precisa de data_conclusao (VAL-07)."""
    tarefa = nova_tarefa(data_conclusao=None)

    with pytest.raises(TaskValidationError, match="exige data_conclusao"):
        analyze_tasks([tarefa])


@pytest.mark.parametrize(
    "campo", ["id_tarefa", "data_criacao", "prazo", "prioridade", "status"]
)
def test_cenario2_campo_obrigatorio_ausente(
    nova_tarefa: FabricaDeTarefa, campo: str
) -> None:
    """Falta de campo obrigatório dispara TaskValidationError (VAL-02)."""
    tarefa = nova_tarefa()
    del tarefa[campo]

    with pytest.raises(TaskValidationError, match=campo):
        analyze_tasks([tarefa])


@pytest.mark.parametrize("id_invalido", [0, -1, "1", 1.5, True])
def test_cenario2_id_invalido(
    nova_tarefa: FabricaDeTarefa, id_invalido: Any
) -> None:
    """id_tarefa precisa ser inteiro maior que zero (VAL-03)."""
    with pytest.raises(TaskValidationError, match="id_tarefa"):
        analyze_tasks([nova_tarefa(id_tarefa=id_invalido)])


def test_cenario2_id_repetido(nova_tarefa: FabricaDeTarefa) -> None:
    """id_tarefa repetido dispara TaskValidationError (VAL-03)."""
    tarefas = [nova_tarefa(id_tarefa=5), nova_tarefa(id_tarefa=5)]

    with pytest.raises(TaskValidationError, match="repetido"):
        analyze_tasks(tarefas)


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("data_criacao", "2026-09-01 08:00"),
        ("prazo", 1756713600),
        ("data_conclusao", "ontem"),
    ],
)
def test_cenario2_data_que_nao_e_datetime(
    nova_tarefa: FabricaDeTarefa, campo: str, valor: Any
) -> None:
    """Datas precisam ser objetos datetime (VAL-04)."""
    with pytest.raises(TaskValidationError, match=f"{campo} deve ser"):
        analyze_tasks([nova_tarefa(**{campo: valor})])


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("prioridade", "urgente"),
        ("prioridade", "media"),
        ("status", "em andamento"),
        ("status", 1),
    ],
)
def test_cenario2_valor_fora_do_permitido(
    nova_tarefa: FabricaDeTarefa, campo: str, valor: Any
) -> None:
    """Prioridade e status só aceitam os valores do contrato (VAL-05)."""
    with pytest.raises(TaskValidationError, match=f"{campo} inválido"):
        analyze_tasks([nova_tarefa(**{campo: valor})])


@pytest.mark.parametrize("entrada", [None, "tarefas", {"id_tarefa": 1}])
def test_cenario2_entrada_que_nao_e_lista(entrada: Any) -> None:
    """A entrada precisa ser uma lista de tarefas (VAL-01)."""
    with pytest.raises(TaskValidationError, match="lista de tarefas"):
        analyze_tasks(entrada)


def test_cenario2_item_que_nao_e_dicionario() -> None:
    """Cada item da lista precisa ser um dicionário (VAL-01)."""
    with pytest.raises(TaskValidationError, match="dicionário"):
        analyze_tasks([42])  # type: ignore[list-item]


def test_cenario2_excecao_especifica() -> None:
    """TaskValidationError é uma exceção própria, derivada de ValueError."""
    assert issubclass(TaskValidationError, ValueError)
    assert TaskValidationError is not ValueError


# ---------------------------------------------------------------------------
# Casos de borda — sem tarefas concluídas e fuso horário
# ---------------------------------------------------------------------------


def test_borda_entrada_vazia_retorna_zeros() -> None:
    """Lista vazia: tudo zerado, sem exceção e sem divisão por zero (RN-06)."""
    resultado = analyze_tasks([])

    esperado = {
        **METRICAS_ZERADAS,
        "indicadores_por_prioridade": {
            "baixa": METRICAS_ZERADAS,
            "média": METRICAS_ZERADAS,
            "alta": METRICAS_ZERADAS,
        },
    }
    assert resultado == esperado


def test_borda_apenas_pendentes_retorna_medias_zeradas(
    nova_tarefa: FabricaDeTarefa,
) -> None:
    """Só pendentes: contagens corretas e 0.0 nas médias (RN-06)."""
    tarefas = [
        nova_tarefa(id_tarefa=1, data_conclusao=None, status="pendente"),
        nova_tarefa(
            id_tarefa=2,
            data_conclusao=None,
            prioridade="baixa",
            status="pendente",
        ),
    ]

    resultado = analyze_tasks(tarefas)

    assert resultado["total_tarefas"] == 2
    assert resultado["total_pendentes"] == 2
    assert resultado["total_concluidas"] == 0
    assert resultado["tempo_medio_conclusao_horas"] == 0.0
    assert resultado["taxa_atraso_percentual"] == 0.0
    for metricas in resultado["indicadores_por_prioridade"].values():
        assert metricas["tempo_medio_conclusao_horas"] == 0.0
        assert metricas["taxa_atraso_percentual"] == 0.0


def test_borda_apenas_canceladas_retorna_medias_zeradas(
    nova_tarefa: FabricaDeTarefa,
) -> None:
    """Só canceladas: não há concluídas, então as médias são 0.0 (RN-06)."""
    tarefa = nova_tarefa(data_conclusao=None, status="cancelada")

    resultado = analyze_tasks([tarefa])

    assert resultado["total_canceladas"] == 1
    assert resultado["tempo_medio_conclusao_horas"] == 0.0
    assert resultado["taxa_atraso_percentual"] == 0.0


def test_borda_datas_sem_fuso_sao_tratadas_como_utc(
    nova_tarefa: FabricaDeTarefa,
) -> None:
    """Datas sem fuso equivalem às mesmas datas em UTC (RN-08)."""
    com_fuso = nova_tarefa()
    sem_fuso = {
        campo: valor.replace(tzinfo=None)
        if isinstance(valor, datetime)
        else valor
        for campo, valor in com_fuso.items()
    }

    assert analyze_tasks([sem_fuso]) == analyze_tasks([com_fuso])


def test_borda_datas_em_outro_fuso_sao_convertidas_para_utc(
    nova_tarefa: FabricaDeTarefa,
) -> None:
    """Conclusão às 9h de Brasília (UTC-3) equivale às 12h UTC (RN-08)."""
    brasilia = timezone(timedelta(hours=-3))
    tarefa = nova_tarefa(
        data_conclusao=datetime(2026, 9, 1, 9, tzinfo=brasilia),
        prazo=utc(1, 11),
    )

    resultado = analyze_tasks([tarefa])

    assert resultado["tempo_medio_conclusao_horas"] == 3.0
    assert resultado["taxa_atraso_percentual"] == 100.0
