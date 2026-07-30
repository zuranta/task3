@description('Object ID of the principal to grant access to: the developer\'s az-login identity for this local-only iteration, swapped for an App Service managed identity\'s principalId with no other change once deployment is added.')
param principalId string

@description('Principal type — defaults to User for the local az-login case; set to ServicePrincipal once an App Service managed identity is used.')
param principalType string = 'User'

@description('Name of the existing Azure OpenAI resource being reused (not provisioned by this project).')
param existingOpenAiName string

var cognitiveServicesOpenAiUserRoleId = '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'

// Deployed via a module whose `scope` targets existingOpenAiResourceGroup (see
// main.bicep) -- a role assignment on a resource in a *different* resource group
// than the deploying file's own scope must be created by a module deployed at
// that resource's scope; it cannot be attached to an `existing` cross-RG resource
// reference from within a module deployed at the caller's own scope (BCP139).
resource openAiAccount 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
  name: existingOpenAiName
}

resource cognitiveServicesOpenAiUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(openAiAccount.id, principalId, cognitiveServicesOpenAiUserRoleId)
  scope: openAiAccount
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      cognitiveServicesOpenAiUserRoleId
    )
    principalId: principalId
    principalType: principalType
  }
}
