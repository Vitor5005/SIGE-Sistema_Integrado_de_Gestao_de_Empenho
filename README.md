# S.I.G.E — Sistema Integrado de Gestão de Empenho 🍽️

> **Plataforma centralizada para gestão de aquisições e fluxo orçamentário do Restaurante Universitário (UFAC).**

![Status](https://img.shields.io/badge/status-em_desenvolvimento-green?style=for-the-badge)
![Local](https://img.shields.io/badge/local-Rio_Branco--AC-red?style=for-the-badge)
![License](https://img.shields.io/badge/license-MIT%20%2F%20BSD%20%2F%20GPL-lightgrey?style=for-the-badge)

---

## 📑 Tabela de Conteúdos
- [Visão Geral](#-visão-geral)
- [Especificações Técnicas](#-especificações-técnicas)
- [Detalhamento de Requisitos](#-detalhamento-de-requisitos)
- [Equipe de Desenvolvimento](#-equipe-de-desenvolvimento)

---

## 📖 Visão Geral

O **S.I.G.E** é uma solução de software projetada para modernizar a gestão do Restaurante Universitário da **Universidade Federal do Acre (UFAC)**. O foco do sistema é o domínio da aquisição de gêneros alimentícios, substituindo processos manuais e planilhas descentralizadas que geravam erros de busca e falta de controle orçamentário.

### Objetivos Principais:
* **Centralização:** Interligar Licitação, ARP, Empenho e Ordens de Entrega.
* **Integridade:** Impedir a reserva de saldos superiores ao disponível em Ata (ARP).
* **Auditabilidade:** Rastrear cada inclusão, reforço ou anulação de empenho.

---

## 🛠️ Especificações Técnicas

A stack tecnológica foi escolhida visando a futura integração com os sistemas do **NTI (Núcleo de Tecnologia da Informação)** da UFAC:

* **Linguagem:** ![Python](https://img.shields.io/badge/python-3670A0?style=flat-square&logo=python&logoColor=ffdd54) (Licença PSFL)
* **Backend:** ![Django](https://img.shields.io/badge/django-%23092e20.svg?style=flat-square&logo=django&logoColor=white) (Licença BSD)
* **Frontend:** ![Angular](https://img.shields.io/badge/Angular-%23DD0031.svg?style=flat-square&logo=angular&logoColor=white) (Licença MIT)
* **Banco de Dados:** ![MySQL](https://img.shields.io/badge/mysql-%2300f.svg?style=flat-square&logo=mysql&logoColor=white) (Licença GPL)
* **Modelagem:** MySQL Workbench
* **IDE:** Visual Studio Code

---

## 📋 Detalhamento de Requisitos

### Requisitos Funcionais (RF)
* **[1] Gestão de Licitação:** Cadastro de editais, fornecedores e catálogo de produtos (unidade de medida, categoria e valor).
* **[2] ARP (Ata de Registro de Preços):** Geração automática de atas por fornecedor, permitindo o acompanhamento do saldo financeiro total.
* **[3] Operações de Empenho:**
    * **Inclusão:** Criação da reserva inicial de saldo (Mínimo de 1.00 unidade).
    * **Reforço:** Adição de saldo a itens já empenhados.
    * **Anulação:** Devolução total ou parcial do saldo do empenho para a ARP.
* **[4] Ordem de Entrega:** Registro da entrega física. Itens solicitados mas não entregues ("sobras") retornam automaticamente ao saldo do empenho.

### Requisitos Não Funcionais (RNF)
* **[1] API de Integração:** Disponibilidade de endpoints para sistemas externos (Estoque/Contabilidade).
* **[2] Interface Padronizada:** UX focada na clareza visual para processos administrativos complexos.
---

## Diagrama Entidade Relacionamento (DER)

<img src="Artefatos\DER\Sige-Diagrama-Entidade-Relacionamento.png" alt="Imagem do DER do sistema SIGE">

## Modelo .env 

DB_NAME=sige
DB_USER=root
DB_PASSWORD=root
DB_HOST=db
DB_PORT=3306

DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@gmail.com
DJANGO_SUPERUSER_PASSWORD=admin

DEBUG=True
DJANGO_SECRET_KEY=chave_super_secreta_aqui


## 👥 Equipe de Desenvolvimento

* **Andrey da Cunha Marques**
* **Carlos Eduardo Marin Bezerra**
* **Gabriela Santos de Oliveira**
* **João Vitor Ferreira da Silva**
* **Marcos Antonio da Silva Manuares**

---

**Rio Branco - AC, 2026**