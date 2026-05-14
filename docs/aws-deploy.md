# Deploy AWS

Arquitetura criada pelo `template.yaml`:

```text
React/Vite -> API Gateway HTTP API -> Lambda Python -> DynamoDB
```

## Pre-requisitos

Instale e configure:

- Python 3.12
- AWS CLI
- AWS SAM CLI
- Credenciais AWS com permissao para Lambda, API Gateway, CloudFormation, IAM e DynamoDB

Confirme o ambiente:

```powershell
python --version
aws sts get-caller-identity
sam --version
```

## Deploy guiado

Na pasta `C:\workspace\totalhub-lambda`:

```powershell
sam build
sam deploy --guided --parameter-overrides AllowedOrigin=http://localhost:5173
```

Para producao, troque o origin:

```powershell
sam deploy --guided --parameter-overrides AllowedOrigin=https://seu-dominio.com.br
```

No fim do deploy, o CloudFormation mostra o output `DemoRequestApiUrl`.

## Conectar com o front

No projeto `C:\workspace\totalhub`, crie ou atualize `.env.local`:

```env
VITE_DEMO_REQUEST_API_URL=https://sua-api.execute-api.sa-east-1.amazonaws.com/solicitar-demonstracao
```

Reinicie o Vite depois de alterar variaveis `VITE_*`.

## Testar endpoint publicado

```powershell
curl -Method POST `
  -Uri "https://sua-api.execute-api.sa-east-1.amazonaws.com/solicitar-demonstracao" `
  -ContentType "application/json" `
  -Body '{"name":"Cliente TotalHub","phone":"(11) 99999-0000","email":"cliente@empresa.com","message":"Quero conhecer a plataforma.","source":"totalhub-site"}'
```

Resposta esperada:

```json
{
  "message": "Solicitacao recebida com sucesso.",
  "requestId": "uuid-da-solicitacao"
}
```

## Onde ver os dados

As solicitacoes sao salvas na tabela DynamoDB criada pelo stack. A chave primaria e `id`.

Tambem da para acompanhar a execucao pelo CloudWatch Logs da funcao `DemoRequestFunction`.
