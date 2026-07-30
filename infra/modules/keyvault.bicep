@description('Name for the new Key Vault. Holds the JWT signing secret (generated here) and the LangSmith API key (set manually post-provision, see quickstart.md).')
param keyVaultName string

@description('Azure region for the Key Vault.')
param location string = resourceGroup().location

@description('Azure AD tenant ID for the vault.')
param tenantId string = subscription().tenantId

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  properties: {
    tenantId: tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
  }
}

// Generated at provision time so no human ever has to invent or transcribe a JWT
// signing secret; resolved at runtime via DefaultAzureCredential (constitution
// Principle II) rather than ever being written to a config file. Concatenated from
// three independent uniqueString()/guid() values (13 + 13 + 36 chars) so the result
// comfortably exceeds the 32-byte minimum RFC 7518 recommends for an HS256 key.
var generatedJwtSecret = '${uniqueString(subscription().subscriptionId, resourceGroup().id, keyVaultName, deployment().name)}${uniqueString(deployment().name, keyVaultName, 'salt2')}${guid(subscription().subscriptionId, resourceGroup().id, keyVaultName)}'

resource jwtSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'JwtSigningSecret'
  properties: {
    value: generatedJwtSecret
  }
}

output keyVaultId string = keyVault.id
output keyVaultName string = keyVault.name
output keyVaultUri string = keyVault.properties.vaultUri
