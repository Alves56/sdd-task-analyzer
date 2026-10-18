# CONTEXT_RULES — Regras de governança para agentes de IA

Estas regras devem ser fornecidas ao assistente de IA **antes** de qualquer
geração ou alteração de código neste repositório. Elas funcionam como
restrições permanentes para manter alinhamento, consistência, segurança e
qualidade. Este arquivo é a fonte de verdade para os agentes de IA, junto com o
contrato em `specs/task_analyzer_spec.md`.

## 1. Diretrizes arquiteturais obrigatórias

- Utilizar Python 3.11 ou superior.
- Utilizar type hints em todas as funções, métodos e parâmetros.
- Seguir a PEP 8 e boas práticas de código limpo.
- Adotar docstrings no estilo Google em módulos, classes e funções.
- Manter funções pequenas, coesas e com um único propósito (Single
  Responsibility Principle).
- Realizar tratamento de exceções específico, com mensagens claras
  (`TaskValidationError` para entradas fora do contrato).
- Prevenir explicitamente a divisão por zero.
- Utilizar logs estruturados com o módulo padrão `logging`.
- Produzir código legível e manutenível, com nomes descritivos.

## 2. Proibições explícitas

- Não utilizar bibliotecas externas não autorizadas. O código de produção usa
  apenas a biblioteca padrão; a única dependência autorizada é o `pytest`, para
  os testes (`requirements.txt`).
- Não alterar, remover ou adaptar os cenários de teste fornecidos.
- Não modificar a estrutura de pastas definida na especificação.
- Não persistir dados em arquivos ou bancos de dados.
- Não alterar a assinatura (nome e parâmetros) das funções públicas sem
  autorização.
- Não gerar código sem testes correspondentes para novas funcionalidades.
- Não inserir código duplicado ou desnecessário.
- Não assumir comportamentos não especificados no contrato de negócio. Em caso
  de lacuna ou conflito, a IA deve apontar o problema e aguardar a decisão
  humana, que é registrada como nova versão da especificação.

## 3. Regras de interação com a IA

- Fornecer sempre o contexto completo (este arquivo e a especificação) antes
  da solicitação.
- Validar se a IA compreendeu o contrato antes de pedir a geração de código.
- Solicitar explicações quando houver dúvidas na solução proposta.
- Revisar criticamente todo código gerado.
- Rejeitar respostas que violem as proibições explícitas ou o contrato.
- Manter este arquivo como fonte de verdade para os agentes de IA.

## 4. Checklist de homologação humana

Todo código gerado por IA só é aceito e versionado depois deste checklist,
registrado na descrição ou na revisão do Pull Request:

1. Executar todos os testes automatizados (`python -m pytest -v`) com 100% de
   aprovação.
2. Conferir a conformidade com o contrato (`specs/task_analyzer_spec.md`) e
   com este arquivo.
3. Avaliar qualidade, legibilidade, tratamento de erros e aderência aos
   padrões (type hints, docstrings, PEP 8, ausência de dependências externas).
4. Executar testes manuais complementares em casos de borda, quando necessário.
5. Somente após a aprovação humana, fazer o merge na branch `main`.

A IA é uma ferramenta de execução e apoio à produtividade. A decisão de aceite,
a homologação e a responsabilidade técnica são humanas.

## 5. Versionamento

- Branch principal `main` e branches de funcionalidade `feature/*`.
- Commits pequenos, frequentes e com mensagens descritivas
  (`feat:`, `test:`, `docs:`, `chore:`).
- Todo código chega à `main` por Pull Request revisado.
- Tags para entregas importantes (ex.: `v0.2.0` ao fim da Fase 2).
