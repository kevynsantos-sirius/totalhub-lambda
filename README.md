# TotalHub Lambda

Aplicacao Python para receber o formulario de solicitacao de demonstracao do TotalHub via API Gateway + Lambda.

## Contrato da API

Endpoint:

```text
POST /solicitar-demonstracao
```

Payload esperado:

```json
{
  "name": "Nome do cliente",
  "phone": "(00) 00000-0000",
  "email": "cliente@empresa.com",
  "message": "Mensagem digitada no formulario",
  "source": "totalhub-site",
  "submittedAt": "2026-05-14T15:00:00.000Z"
}
```

Resposta de sucesso:

```json
{
  "message": "Solicitacao recebida com sucesso.",
  "requestId": "uuid-da-solicitacao"
}
```

## Rodar testes

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest
```

## Testar localmente com SAM

```powershell
sam build
sam local invoke DemoRequestFunction --event events/demo-request.json
sam local start-api
```

Com `sam local start-api`, configure o front em `C:\workspace\totalhub\.env.local`:

```env
VITE_DEMO_REQUEST_API_URL=http://127.0.0.1:3000/solicitar-demonstracao
```

## Deploy na AWS

Primeiro configure as credenciais AWS no ambiente local. Depois rode:

```powershell
sam build
sam deploy --guided --parameter-overrides AllowedOrigin=https://seu-dominio.com.br
```

Ao final, copie o output `DemoRequestApiUrl` para a variavel `VITE_DEMO_REQUEST_API_URL` do front.

Veja tambem [docs/aws-deploy.md](docs/aws-deploy.md) para o passo a passo de publicacao e teste do endpoint.

## Variaveis de ambiente

`ALLOWED_ORIGIN`: origem aceita no CORS. Para desenvolvimento, use `http://localhost:5173`. Em producao, use o dominio real.

`DEMO_REQUESTS_TABLE`: nome da tabela DynamoDB. O `template.yaml` cria e injeta essa variavel automaticamente. Sem ela, a Lambda apenas registra a solicitacao no log.
