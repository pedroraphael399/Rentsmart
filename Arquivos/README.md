# RentSmart — Sistema de Orçamento de Locação (R.M Imóveis)

Aplicação em Python, orientada a objetos, que calcula o orçamento mensal de locação de apartamentos, casas e estúdios, apresenta um resumo detalhado e gera um arquivo CSV com a projeção de pagamentos dos 12 primeiros meses.

## Requisitos

- Python **3.10 ou superior** (usa apenas a biblioteca padrão; não é preciso instalar nada).

## Como executar

```bash
git clone <URL-DO-SEU-REPOSITORIO>
cd rentsmart
python rentsmart.py
```

(No Windows, se `python` não funcionar, tente `py rentsmart.py`.)

O programa pergunta, passo a passo:

1. A categoria do imóvel (apartamento, casa ou estúdio);
2. Quartos (1 ou 2) e garagem — para apartamentos e casas;
3. Se o cliente possui crianças — somente para apartamentos;
4. Quantidade de vagas de estacionamento — somente para estúdios;
5. Em quantas parcelas (1 a 5) será paga a taxa contratual.

Ao final, exibe o orçamento na tela e grava `projecao_12_meses.csv` na pasta atual. Um exemplo do arquivo gerado está em `exemplo_projecao_12_meses.csv`.

## Como executar os testes

```bash
python -m unittest -v
```

## Regras de negócio implementadas

| Item | Regra |
|---|---|
| Apartamento | Base R$ 700,00 · 2 quartos: +R$ 200,00 · garagem: +R$ 300,00 |
| Casa | Base R$ 900,00 · 2 quartos: +R$ 250,00 · garagem: +R$ 300,00 |
| Estúdio | Base R$ 1.200,00 · pacote de 2 vagas: R$ 250,00 · vaga extra: R$ 60,00 cada |
| Desconto | Apenas apartamentos: 5% sobre (base + adicionais) se o cliente **não** tem crianças |
| Taxa contratual | R$ 2.000,00, cobrada à parte do aluguel, em 1 a 5 parcelas |

### Premissas adotadas

- No estúdio, a garagem é opcional: 0 vagas = sem custo; 1 ou 2 vagas = pacote de R$ 250,00; a partir da 3ª vaga soma-se R$ 60,00 por vaga extra.
- Quando a taxa não divide em centavos exatos (ex.: 3 parcelas), a última parcela absorve a diferença para o total fechar em R$ 2.000,00.
- Na projeção, as parcelas da taxa são cobradas nos primeiros meses do contrato, junto com o aluguel.
- Os valores usam `Decimal` (e não `float`) para evitar erros de arredondamento em dinheiro.

## Formato do CSV

Separador `;`, vírgula decimal e codificação UTF-8 com BOM, para abrir direto no Excel em português do Brasil.

| Mês | Aluguel (R$) | Parcela da taxa contratual (R$) | Total do mês (R$) | Total acumulado (R$) |
|---|---|---|---|---|

## Estrutura do projeto

Todo o programa está em **um único arquivo**, `rentsmart.py`, dividido em partes comentadas:

```
rentsmart/
├── rentsmart.py                  # programa completo (6 partes comentadas, abaixo)
├── test_rentsmart.py             # testes automatizados (opcional)
├── exemplo_projecao_12_meses.csv # exemplo de saída
└── README.md
```

| Parte | Conteúdo |
|---|---|
| 1 | Formatação de valores em reais |
| 2 | Classes dos imóveis: `Imovel`, `ImovelComQuartos`, `Apartamento`, `Casa`, `Estudio` |
| 3 | Classe `Orcamento`: aluguel mensal, parcelas da taxa e projeção de 12 meses |
| 4 | Classe `ExportadorCSV`: gera o arquivo CSV |
| 5 | Entrada de dados e validação (menus e perguntas) |
| 6 | Programa principal (`main`) que une tudo |

## Orientação a Objetos na solução

- **Herança e abstração:** `Imovel` é uma classe abstrata; `ImovelComQuartos` concentra a regra comum de casas e apartamentos; `Apartamento`, `Casa` e `Estudio` especializam o que é diferente.
- **Polimorfismo:** `Orcamento` chama `adicionais()` e `desconto()` sem saber qual tipo de imóvel recebeu; cada classe aplica a própria regra.
- **Encapsulamento / responsabilidade única:** `Orcamento` calcula, `ExportadorCSV` grava arquivos, as funções `ler_*` validam entradas e `main()` apenas coordena.
