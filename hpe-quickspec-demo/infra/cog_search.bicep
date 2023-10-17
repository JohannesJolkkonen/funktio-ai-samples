param location string = 'eastus'
param resourceName string = 'cogsearch-hpe'
param skuName string = 'Free' // Change to the desired SKU (e.g., Basic, Standard, etc.)

resource searchService 'Microsoft.Search/searchServices@2022-09-01' = {
  name: resourceName
  location: location
  sku: {
    name: skuName
  }
  identity: {
    type: 'SystemAssigned'
  }
}

output searchServiceEndpoint string = searchService.properties.status
