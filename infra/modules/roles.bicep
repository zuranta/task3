@description('Object ID of the principal to grant access to: the developer\'s az-login identity for this local-only iteration, swapped for an App Service managed identity\'s principalId with no other change once deployment is added.')
param principalId string

@description('Principal type — defaults to User for the local az-login case; set to ServicePrincipal once an App Service managed identity is used.')
param principalType string = 'User'

param searchServiceName string
param keyVaultName string
param appInsightsName string

var searchIndexDataContributorRoleId = '8ebe5a00-799e-43f5-93ac-243d3dce84a7'
var searchIndexDataReaderRoleId = '1407120a-92aa-4202-b7e9-c0e197c71c8f'
var keyVaultSecretsUserRoleId = '4633458b-17de-408a-b874-0445c86b69e6'
var monitoringReaderRoleId = '43d0d8ad-25c7-4714-9337-8ba259a9fe05'

resource searchService 'Microsoft.Search/searchServices@2024-06-01-preview' existing = {
  name: searchServiceName
}

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: appInsightsName
}

// Cognitive Services OpenAI User (on the *existing* Azure OpenAI resource, which
// may live in a different resource group) is granted by the openai-role.bicep
// module instead, deployed with `scope: resourceGroup(existingOpenAiResourceGroup)`
// from main.bicep -- see that module's comment for why this can't live here.

resource searchIndexDataContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(searchService.id, principalId, searchIndexDataContributorRoleId)
  scope: searchService
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', searchIndexDataContributorRoleId)
    principalId: principalId
    principalType: principalType
  }
}

resource searchIndexDataReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(searchService.id, principalId, searchIndexDataReaderRoleId)
  scope: searchService
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', searchIndexDataReaderRoleId)
    principalId: principalId
    principalType: principalType
  }
}

resource keyVaultSecretsUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, principalId, keyVaultSecretsUserRoleId)
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', keyVaultSecretsUserRoleId)
    principalId: principalId
    principalType: principalType
  }
}

// Read access to Application Insights' own logs/metrics (dependencies/requests
// tables), so metrics_service.py's query_resource() calls succeed (FR-027/028,
// User Story 5) -- distinct from the JWT/LangSmith secrets above.
resource monitoringReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(appInsights.id, principalId, monitoringReaderRoleId)
  scope: appInsights
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', monitoringReaderRoleId)
    principalId: principalId
    principalType: principalType
  }
}
