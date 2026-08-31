targetScope = 'resourceGroup'

param name string
param location string = resourceGroup().location
param tags object = {}
param principalId string
param principalName string
param clientIpAddress string = ''

var allowPublicClient = !empty(clientIpAddress)

resource server 'Microsoft.Sql/servers@2022-05-01-preview' = {
  name: name
  location: location
  tags: tags
  properties: {
    administrators: {
      administratorType: 'ActiveDirectory'
      principalType: 'User'
      login: principalName
      sid: principalId
      tenantId: subscription().tenantId
      azureADOnlyAuthentication: true
    }
    minimalTlsVersion: '1.2'
    publicNetworkAccess: allowPublicClient ? 'Enabled' : 'Disabled'
    restrictOutboundNetworkAccess: 'Enabled'
  }
}

resource database 'Microsoft.Sql/servers/databases@2022-05-01-preview' = {
  parent: server
  name: 'oracle-migration-demo'
  location: location
  tags: tags
  sku: {
    name: 'Basic'
    tier: 'Basic'
    capacity: 5
  }
  properties: {
    collation: 'SQL_Latin1_General_CP1_CI_AS'
    maxSizeBytes: 2147483648
  }
}

resource clientFirewallRule 'Microsoft.Sql/servers/firewallRules@2022-05-01-preview' = if (allowPublicClient) {
  parent: server
  name: 'DemoClient'
  properties: {
    startIpAddress: clientIpAddress
    endIpAddress: clientIpAddress
  }
}

output serverFqdn string = server.properties.fullyQualifiedDomainName
output databaseName string = database.name

