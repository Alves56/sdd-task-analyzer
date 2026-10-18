"""TaskAnalyzer: métricas de produtividade a partir de registros de tarefas.

Implementa o contrato de ``specs/task_analyzer_spec.md`` (versão 1.1) seguindo
as regras de ``CONTEXT_RULES.md``: Python 3.11+, type hints em todas as
funções, docstrings no estilo Google, exceção específica para entradas
inválidas, prevenção explícita de divisão por zero, logs estruturados com
``logging`` e nenhuma dependência fora da biblioteca padrão.

Exemplo:
    >>> from datetime import UTC, datetime
    >>> tarefa = {
    ...     "id_tarefa": 1,
    ...     "data_criacao": datetime(2026, 9, 1, 8, tzinfo=UTC),
    ...     "data_inicio": datetime(2026, 9, 1, 9, tzinfo=UTC),
    ...     "data_conclusao": datetime(2026, 9, 1, 11, tzinfo=UTC),
    ...     "prazo": datetime(2026, 9, 1, 12, tzinfo=UTC),
    ...     "prioridade": "alta",
    ...     "status": "concluída",
    ... }
    >>> analyze_tasks([tarefa])["tempo_medio_conclusao_horas"]
    2.0
"""

import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Final, NoReturn, TypedDict

__all__ = [
    "MetricasTarefas",
    "ResultadoAnalise",
    "TaskValidationError",
    "analyze_tasks",
]

logger = logging.getLogger(__name__)

PRIORIDADES: Final[tuple[str, ...]] = ("baixa", "média", "alta")
STATUS_CONCLUIDA: Final[str] = "concluída"
STATUS_PENDENTE: Final[str] = "pendente"
STATUS_CANCELADA: Final[str] = "cancelada"
STATUS_VALIDOS: Final[tuple[str, ...]] = (
    STATUS_CONCLUIDA,
    STATUS_PENDENTE,
    STATUS_CANCELADA,
)
CAMPOS_OBRIGATORIOS: Final[tuple[str, ...]] = (
    "id_tarefa",
    "data_criacao",
    "prazo",
    "prioridade",
    "status",
)
SEGUNDOS_POR_HORA: Final[int] = 3600
DUAS_CASAS: Final[Decimal] = Decimal("0.01")


class TaskValidationError(ValueError):
    """Entrada fora do contrato do TaskAnalyzer.

    Lançada quando falta um campo obrigatório, um valor tem tipo ou conteúdo
    inválido, um ``id_tarefa`` se repete ou as datas de uma tarefa são
    inconsistentes. A mensagem identifica a tarefa e o problema.
    """


class MetricasTarefas(TypedDict):
    """Métricas de um grupo de tarefas (geral ou de uma prioridade)."""

    total_tarefas: int
    total_concluidas: int
    total_pendentes: int
    total_canceladas: int
    tempo_medio_conclusao_horas: float
    taxa_atraso_percentual: float


class ResultadoAnalise(MetricasTarefas):
    """Resultado de ``analyze_tasks``: métricas gerais e por prioridade."""

    indicadores_por_prioridade: dict[str, MetricasTarefas]


@dataclass(frozen=True, slots=True)
class _Tarefa:
    """Tarefa validada, com todas as datas normalizadas para UTC."""

    id_tarefa: int
    data_criacao: datetime
    data_inicio: datetime | None
    data_conclusao: datetime | None
    prazo: datetime
    prioridade: str
    status: str


@dataclass(frozen=True, slots=True)
class _Conclusao:
    """Dados de uma tarefa concluída usados no tempo médio e no atraso."""

    inicio: datetime
    fim: datetime
    prazo: datetime

    @property
    def horas(self) -> float:
        """Tempo de conclusão em horas (RN-02 e RN-03)."""
        return (self.fim - self.inicio).total_seconds() / SEGUNDOS_POR_HORA

    @property
    def atrasada(self) -> bool:
        """Indica se a conclusão ocorreu depois do prazo (RN-04)."""
        return self.fim > self.prazo


def analyze_tasks(tasks: Sequence[Mapping[str, Any]]) -> ResultadoAnalise:
    """Calcula as métricas de produtividade de uma lista de tarefas.

    Args:
        tasks: Tarefas a analisar. Cada item é um dicionário com os campos
            da seção 3 da especificação.

    Returns:
        Totais por status, tempo médio de conclusão em horas e taxa de atraso
        percentual, no geral e em ``indicadores_por_prioridade``.

    Raises:
        TaskValidationError: Se a entrada violar o contrato (seção 6 da
            especificação), por exemplo com datas inconsistentes.
    """
    tarefas = _validar_entrada(tasks)
    gerais = _calcular_metricas(tarefas)
    por_prioridade = {
        prioridade: _calcular_metricas(
            [tarefa for tarefa in tarefas if tarefa.prioridade == prioridade]
        )
        for prioridade in PRIORIDADES
    }
    logger.info("analise_concluida", extra={"metricas": dict(gerais)})
    return {**gerais, "indicadores_por_prioridade": por_prioridade}


def _validar_entrada(tasks: Sequence[Mapping[str, Any]]) -> list[_Tarefa]:
    """Valida a lista recebida e cada uma das tarefas (VAL-01 a VAL-07).

    Args:
        tasks: Entrada recebida por ``analyze_tasks``.

    Returns:
        Tarefas validadas, na mesma ordem da entrada.

    Raises:
        TaskValidationError: Se a entrada ou alguma tarefa for inválida.
    """
    if not isinstance(tasks, (list, tuple)):
        _rejeitar("A entrada deve ser uma lista de tarefas.")
    tarefas = [
        _validar_tarefa(registro, indice)
        for indice, registro in enumerate(tasks)
    ]
    _verificar_ids_unicos(tarefas)
    return tarefas


def _validar_tarefa(registro: Mapping[str, Any], indice: int) -> _Tarefa:
    """Valida uma tarefa e converte suas datas para UTC.

    Args:
        registro: Dicionário com os campos da tarefa.
        indice: Posição da tarefa na lista, usada nas mensagens de erro.

    Returns:
        A tarefa validada.

    Raises:
        TaskValidationError: Se a tarefa violar o contrato.
    """
    if not isinstance(registro, Mapping):
        _rejeitar(f"Tarefa no índice {indice}: deve ser um dicionário.")
    _verificar_campos_obrigatorios(registro, indice)
    tarefa = _Tarefa(
        id_tarefa=_validar_id(registro["id_tarefa"], indice),
        data_criacao=_para_utc(
            registro["data_criacao"], "data_criacao", indice
        ),
        data_inicio=_para_utc_opcional(
            registro.get("data_inicio"), "data_inicio", indice
        ),
        data_conclusao=_para_utc_opcional(
            registro.get("data_conclusao"), "data_conclusao", indice
        ),
        prazo=_para_utc(registro["prazo"], "prazo", indice),
        prioridade=_validar_opcao(
            registro["prioridade"], "prioridade", PRIORIDADES, indice
        ),
        status=_validar_opcao(
            registro["status"], "status", STATUS_VALIDOS, indice
        ),
    )
    _verificar_conclusao_informada(tarefa)
    _verificar_ordem_das_datas(tarefa)
    return tarefa


def _verificar_campos_obrigatorios(
    registro: Mapping[str, Any], indice: int
) -> None:
    """Garante que os campos obrigatórios existem e não são ``None`` (VAL-02).

    Args:
        registro: Dicionário com os campos da tarefa.
        indice: Posição da tarefa na lista.

    Raises:
        TaskValidationError: Se faltar algum campo obrigatório.
    """
    ausentes = [
        campo for campo in CAMPOS_OBRIGATORIOS if registro.get(campo) is None
    ]
    if ausentes:
        _rejeitar(
            f"Tarefa no índice {indice}: campo obrigatório ausente: "
            f"{', '.join(ausentes)}."
        )


def _validar_id(valor: Any, indice: int) -> int:
    """Valida o ``id_tarefa``: inteiro maior que zero (VAL-03).

    Args:
        valor: Valor recebido no campo ``id_tarefa``.
        indice: Posição da tarefa na lista.

    Returns:
        O identificador validado.

    Raises:
        TaskValidationError: Se o valor não for um inteiro positivo.
    """
    if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
        _rejeitar(
            f"Tarefa no índice {indice}: id_tarefa deve ser um inteiro "
            f"maior que 0 (recebido: {valor!r})."
        )
    return valor


def _para_utc(valor: Any, campo: str, indice: int) -> datetime:
    """Valida uma data e a converte para UTC (VAL-04 e RN-08).

    Datas sem fuso horário são interpretadas como UTC.

    Args:
        valor: Valor recebido no campo de data.
        campo: Nome do campo, usado na mensagem de erro.
        indice: Posição da tarefa na lista.

    Returns:
        A data em UTC.

    Raises:
        TaskValidationError: Se o valor não for um ``datetime``.
    """
    if not isinstance(valor, datetime):
        _rejeitar(
            f"Tarefa no índice {indice}: {campo} deve ser um datetime "
            f"(recebido: {valor!r})."
        )
    if valor.utcoffset() is None:
        return valor.replace(tzinfo=UTC)
    return valor.astimezone(UTC)


def _para_utc_opcional(
    valor: Any, campo: str, indice: int
) -> datetime | None:
    """Converte para UTC uma data opcional, mantendo ``None`` se ausente.

    Args:
        valor: Valor recebido no campo de data, ou ``None``.
        campo: Nome do campo, usado na mensagem de erro.
        indice: Posição da tarefa na lista.

    Returns:
        A data em UTC, ou ``None`` se não foi informada.

    Raises:
        TaskValidationError: Se o valor existir e não for um ``datetime``.
    """
    if valor is None:
        return None
    return _para_utc(valor, campo, indice)


def _validar_opcao(
    valor: Any, campo: str, permitidos: tuple[str, ...], indice: int
) -> str:
    """Valida um campo de valores fixos, como prioridade e status (VAL-05).

    Args:
        valor: Valor recebido.
        campo: Nome do campo, usado na mensagem de erro.
        permitidos: Valores aceitos pelo contrato.
        indice: Posição da tarefa na lista.

    Returns:
        O valor validado.

    Raises:
        TaskValidationError: Se o valor não estiver entre os permitidos.
    """
    if not isinstance(valor, str) or valor not in permitidos:
        _rejeitar(
            f"Tarefa no índice {indice}: {campo} inválido ({valor!r}); "
            f"valores permitidos: {', '.join(permitidos)}."
        )
    return valor


def _verificar_conclusao_informada(tarefa: _Tarefa) -> None:
    """Exige ``data_conclusao`` em tarefas concluídas (VAL-07).

    Args:
        tarefa: Tarefa validada.

    Raises:
        TaskValidationError: Se a tarefa concluída não tiver data de conclusão.
    """
    if tarefa.status == STATUS_CONCLUIDA and tarefa.data_conclusao is None:
        _rejeitar(
            f"Tarefa {tarefa.id_tarefa}: status '{STATUS_CONCLUIDA}' "
            "exige data_conclusao."
        )


def _verificar_ordem_das_datas(tarefa: _Tarefa) -> None:
    """Rejeita datas inconsistentes entre si (VAL-06).

    Args:
        tarefa: Tarefa validada.

    Raises:
        TaskValidationError: Se uma data posterior for anterior à que deveria
            vir antes dela.
    """
    criacao, inicio, conclusao = (
        tarefa.data_criacao,
        tarefa.data_inicio,
        tarefa.data_conclusao,
    )
    pares = (
        ("data_inicio", inicio, "data_criacao", criacao),
        ("data_conclusao", conclusao, "data_criacao", criacao),
        ("data_conclusao", conclusao, "data_inicio", inicio),
    )
    for campo_depois, depois, campo_antes, antes in pares:
        if depois is not None and antes is not None and depois < antes:
            _rejeitar(
                f"Tarefa {tarefa.id_tarefa}: datas inconsistentes - "
                f"{campo_depois} ({depois.isoformat()}) é anterior a "
                f"{campo_antes} ({antes.isoformat()})."
            )


def _verificar_ids_unicos(tarefas: Sequence[_Tarefa]) -> None:
    """Garante que nenhum ``id_tarefa`` se repete (VAL-03).

    Args:
        tarefas: Tarefas já validadas individualmente.

    Raises:
        TaskValidationError: Se houver identificador repetido.
    """
    vistos: set[int] = set()
    for tarefa in tarefas:
        if tarefa.id_tarefa in vistos:
            _rejeitar(
                f"Tarefa {tarefa.id_tarefa}: id_tarefa repetido; "
                "o identificador deve ser único."
            )
        vistos.add(tarefa.id_tarefa)


def _calcular_metricas(tarefas: Sequence[_Tarefa]) -> MetricasTarefas:
    """Calcula as métricas de um grupo de tarefas (RN-01 a RN-07).

    Args:
        tarefas: Tarefas validadas do grupo (todas ou de uma prioridade).

    Returns:
        Totais por status, tempo médio em horas e taxa de atraso.
    """
    conclusoes = _extrair_conclusoes(tarefas)
    atrasadas = sum(1 for conclusao in conclusoes if conclusao.atrasada)
    return {
        "total_tarefas": len(tarefas),
        "total_concluidas": len(conclusoes),
        "total_pendentes": _contar_status(tarefas, STATUS_PENDENTE),
        "total_canceladas": _contar_status(tarefas, STATUS_CANCELADA),
        "tempo_medio_conclusao_horas": _media(
            [conclusao.horas for conclusao in conclusoes]
        ),
        "taxa_atraso_percentual": _percentual(atrasadas, len(conclusoes)),
    }


def _extrair_conclusoes(tarefas: Sequence[_Tarefa]) -> list[_Conclusao]:
    """Seleciona as concluídas e define o início efetivo (RN-01 e RN-02).

    Sem ``data_inicio``, o tempo é contado a partir de ``data_criacao``.

    Args:
        tarefas: Tarefas validadas.

    Returns:
        Uma ``_Conclusao`` para cada tarefa com status ``concluída``.
    """
    return [
        _Conclusao(
            inicio=(
                tarefa.data_inicio
                if tarefa.data_inicio is not None
                else tarefa.data_criacao
            ),
            fim=tarefa.data_conclusao,
            prazo=tarefa.prazo,
        )
        for tarefa in tarefas
        # data_conclusao is not None já é garantido pela VAL-07; a checagem
        # repetida aqui apenas informa o tipo ao verificador estático.
        if tarefa.status == STATUS_CONCLUIDA
        and tarefa.data_conclusao is not None
    ]


def _contar_status(tarefas: Sequence[_Tarefa], status: str) -> int:
    """Conta as tarefas com determinado status.

    Args:
        tarefas: Tarefas validadas.
        status: Status a contar.

    Returns:
        Quantidade de tarefas com o status informado.
    """
    return sum(1 for tarefa in tarefas if tarefa.status == status)


def _media(valores: Sequence[float]) -> float:
    """Média arredondada, ou 0.0 se não houver valores (RN-06 e RN-07).

    Args:
        valores: Valores a considerar.

    Returns:
        A média com duas casas decimais, ou 0.0 para lista vazia.
    """
    if not valores:
        return 0.0
    return _arredondar(sum(valores) / len(valores))


def _percentual(parte: int, total: int) -> float:
    """Percentual arredondado, ou 0.0 se o total for zero (RN-05 e RN-06).

    Args:
        parte: Quantidade de itens que atendem ao critério.
        total: Quantidade total de itens.

    Returns:
        O percentual com duas casas decimais, ou 0.0 quando ``total`` é zero.
    """
    if total == 0:
        return 0.0
    return _arredondar(parte / total * 100)


def _arredondar(valor: float) -> float:
    """Arredonda para duas casas, com meio para cima (RN-07).

    Args:
        valor: Número a arredondar.

    Returns:
        O número com duas casas decimais (ex.: 1.125 vira 1.13).
    """
    return float(Decimal(str(valor)).quantize(DUAS_CASAS, ROUND_HALF_UP))


def _rejeitar(mensagem: str) -> NoReturn:
    """Registra a falha de validação no log e lança a exceção específica.

    Args:
        mensagem: Descrição clara do problema encontrado.

    Raises:
        TaskValidationError: Sempre.
    """
    logger.warning("entrada_invalida", extra={"motivo": mensagem})
    raise TaskValidationError(mensagem)
