# HH Inventário Online

Aplicação Streamlit para gerar um painel Hora a Hora de Inventário a partir de um único upload de arquivo.

## Como rodar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Como publicar online

### Streamlit Community Cloud
1. Suba esta pasta para um repositório no GitHub.
2. Crie um app no Streamlit Community Cloud apontando para `app.py`.
3. O usuário final precisará apenas fazer upload do arquivo `.xlsx` ou `.csv`.

### Render
1. Crie um novo serviço **Web Service**.
2. Build command:
   ```bash
   pip install -r requirements.txt
   ```
3. Start command:
   ```bash
   streamlit run app.py --server.port $PORT --server.address 0.0.0.0
   ```

## Estrutura esperada do arquivo

Colunas mínimas:
- `Data de Escaneamento`
- `Situação`

Colunas aproveitadas no painel:
- `Operador`
- `Área`
- `Comentário`
- `Pacote`

## Regras do painel

- Lê o arquivo enviado pelo usuário.
- Usa a primeira hora encontrada na base como início da janela.
- Monta 8 colunas horárias sequenciais.
- Gera:
  - resumo por status
  - resumo por operador para Verificados
  - resumo por operador para Deslocado
