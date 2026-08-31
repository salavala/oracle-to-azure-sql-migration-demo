targetScope = 'subscription'

@minLength(1)
@maxLength(64)
param environmentName string

param location string

@description('Object ID of the Microsoft Entra user who will administer Azure SQL.')
param principalId string

@description('Display name or UPN of the Microsoft Entra administrator.')
param principalName string

var resourceSuffix = take(uniqueString(subscription().id, environmentName, location), 6)
var tags = {
  'azd-env-name': environmentName
  workload: 'oracle-migration-demo'
}

resource resourceGroup 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: 'rg-${environmentName}-${resourceSuffix}'
  location: location
  tags: tags
}

module sql './modules/sql.bicep' = {
  name: 'sql'
  scope: resourceGroup
  params: {
    name: 'sql-${environmentName}-${resourceSuffix}'
    location: location
    tags: tags
    principalId: principalId
    principalName: principalName
  }
}

output AZURE_RESOURCE_GROUP string = resourceGroup.name
output AZURE_SQL_SERVER string = sql.outputs.serverFqdn
output AZURE_SQL_DATABASE string = sql.outputs.databaseName
