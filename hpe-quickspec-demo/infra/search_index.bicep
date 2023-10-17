param searchServiceName string
param indexName string = 'your-index-name'

resource searchIndex 'Microsoft.Search/searchServices@2022-09-01' = {
  name: '${searchServiceName}/${indexName}'
  properties: {
    fields: [
      {
        name: 'id'
        type: 'Edm.String'
        key: true
        searchable: false
        filterable: true
        sortable: true
        facetable: true
      }
      {
        name: 'title'
        type: 'Edm.String'
        searchable: true
        filterable: true
        sortable: true
        facetable: false
      }
      {
        name: 'description'
        type: 'Edm.String'
        searchable: true
        filterable: true
        sortable: false
        facetable: false
      }
      // Add more fields as needed
    ]
    suggesters: [
      {
        name: 'sg'
        searchMode: 'analyzingInfixMatching'
        sourceFields: ['title', 'description']
      }
    ]
  }
}
