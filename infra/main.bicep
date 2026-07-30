// Local-only iteration: provisions the one new Azure AI Search resource plus Key Vault
// and Application Insights this project depends on, and grants the developer's own
// az-login identity RBAC access to those new resources and to the existing Azure
// OpenAI resource. No App Service or new Azure OpenAI resource is provisioned here —
// see plan.md's Deployment Scope for the future-amendment path.

targetScope = 'resourceGroup'

@description('Object ID of the principal to grant access to (your `az ad signed-in-user show --query id -o tsv` for local dev).')
param principalId string

@description('Principal type for the role assignments.')
param principalType string = 'User'

@description('Name of the existing Azure OpenAI resource to reuse.')
param existingOpenAiName string = 'aoai-jab4fcusuxtqs'

@description('Resource group containing the existing Azure OpenAI resource.')
param existingOpenAiResourceGroup string = resourceGroup().name

@description('Base name used to derive resource names (Search, Key Vault, Log Analytics, App Insights).')
param baseName string = 'ragqa'

@description('Azure region for all new resources.')
param location string = resourceGroup().location

@description('Azure region for the Search resource specifically -- overridable independently of `location` since Free-tier Search capacity is scarce and not evenly available across regions.')
param searchLocation string = location

var searchServiceName = '${baseName}-search-${uniqueString(resourceGroup().id)}'
var keyVaultName = '${baseName}-kv-${uniqueString(resourceGroup().id)}'
var logAnalyticsName = '${baseName}-logs-${uniqueString(resourceGroup().id)}'
var appInsightsName = '${baseName}-appi-${uniqueString(resourceGroup().id)}'

module search 'modules/search.bicep' = {
  name: 'search-deployment'
  params: {
    searchServiceName: searchServiceName
    location: searchLocation
  }
}

module keyVault 'modules/keyvault.bicep' = {
  name: 'keyvault-deployment'
  params: {
    keyVaultName: keyVaultName
    location: location
  }
}

module monitoring 'modules/monitoring.bicep' = {
  name: 'monitoring-deployment'
  params: {
    logAnalyticsName: logAnalyticsName
    appInsightsName: appInsightsName
    location: location
  }
}

module roles 'modules/roles.bicep' = {
  name: 'roles-deployment'
  params: {
    principalId: principalId
    principalType: principalType
    searchServiceName: search.outputs.searchServiceName
    keyVaultName: keyVault.outputs.keyVaultName
  }
}

// A separate module scoped to the existing Azure OpenAI resource's own resource
// group -- which may differ from this deployment's -- since a role assignment on
// a cross-resource-group resource can only be created by a module deployed at
// that resource's scope (see modules/openai-role.bicep).
module openAiRole 'modules/openai-role.bicep' = {
  name: 'openai-role-deployment'
  scope: resourceGroup(existingOpenAiResourceGroup)
  params: {
    principalId: principalId
    principalType: principalType
    existingOpenAiName: existingOpenAiName
  }
}

output searchEndpoint string = search.outputs.searchEndpoint
output keyVaultUri string = keyVault.outputs.keyVaultUri
output appInsightsConnectionString string = monitoring.outputs.appInsightsConnectionString
