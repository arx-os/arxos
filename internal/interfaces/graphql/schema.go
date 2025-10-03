package graphql

import (
	"github.com/graphql-go/graphql"
)

// Schema represents the GraphQL schema for ArxOS
type Schema struct {
	schema *graphql.Schema
}

// NewSchema creates a new GraphQL schema
func NewSchema(resolvers *Resolvers) (*Schema, error) {
	schema := &Schema{}

	// Define types
	buildingType := schema.getBuildingType()
	equipmentType := schema.getEquipmentType()
	componentType := schema.getComponentType()
	userType := schema.getUserType()
	organizationType := schema.getOrganizationType()
	// floorType := schema.getFloorType()
	// roomType := schema.getRoomType()

	// Define input types
	createBuildingInput := schema.getCreateBuildingInputType()
	updateBuildingInput := schema.getUpdateBuildingInputType()
	createEquipmentInput := schema.getCreateEquipmentInputType()
	updateEquipmentInput := schema.getUpdateEquipmentInputType()
	createUserInput := schema.getCreateUserInputType()
	updateUserInput := schema.getUpdateUserInputType()

	// Define query type
	queryType := graphql.NewObject(graphql.ObjectConfig{
		Name: "Query",
		Fields: graphql.Fields{
			"building": &graphql.Field{
				Type: buildingType,
				Args: graphql.FieldConfigArgument{
					"id": &graphql.ArgumentConfig{
						Type: graphql.NewNonNull(graphql.String),
					},
				},
				Resolve: resolvers.GetBuilding,
			},
			"buildings": &graphql.Field{
				Type: graphql.NewList(buildingType),
				Args: graphql.FieldConfigArgument{
					"limit": &graphql.ArgumentConfig{
						Type: graphql.Int,
					},
					"offset": &graphql.ArgumentConfig{
						Type: graphql.Int,
					},
					"name": &graphql.ArgumentConfig{
						Type: graphql.String,
					},
				},
				Resolve: resolvers.GetBuildings,
			},
			"equipment": &graphql.Field{
				Type: equipmentType,
				Args: graphql.FieldConfigArgument{
					"id": &graphql.ArgumentConfig{
						Type: graphql.NewNonNull(graphql.String),
					},
				},
				Resolve: resolvers.GetEquipment,
			},
			"equipments": &graphql.Field{
				Type: graphql.NewList(equipmentType),
				Args: graphql.FieldConfigArgument{
					"limit": &graphql.ArgumentConfig{
						Type: graphql.Int,
					},
					"offset": &graphql.ArgumentConfig{
						Type: graphql.Int,
					},
					"buildingId": &graphql.ArgumentConfig{
						Type: graphql.String,
					},
					"type": &graphql.ArgumentConfig{
						Type: graphql.String,
					},
				},
				Resolve: resolvers.GetEquipments,
			},
			"component": &graphql.Field{
				Type: componentType,
				Args: graphql.FieldConfigArgument{
					"id": &graphql.ArgumentConfig{
						Type: graphql.NewNonNull(graphql.String),
					},
				},
				Resolve: resolvers.GetComponent,
			},
			"components": &graphql.Field{
				Type: graphql.NewList(componentType),
				Args: graphql.FieldConfigArgument{
					"limit": &graphql.ArgumentConfig{
						Type: graphql.Int,
					},
					"offset": &graphql.ArgumentConfig{
						Type: graphql.Int,
					},
					"buildingId": &graphql.ArgumentConfig{
						Type: graphql.String,
					},
					"type": &graphql.ArgumentConfig{
						Type: graphql.String,
					},
				},
				Resolve: resolvers.GetComponents,
			},
			"user": &graphql.Field{
				Type: userType,
				Args: graphql.FieldConfigArgument{
					"id": &graphql.ArgumentConfig{
						Type: graphql.NewNonNull(graphql.String),
					},
				},
				Resolve: resolvers.GetUser,
			},
			"users": &graphql.Field{
				Type: graphql.NewList(userType),
				Args: graphql.FieldConfigArgument{
					"limit": &graphql.ArgumentConfig{
						Type: graphql.Int,
					},
					"offset": &graphql.ArgumentConfig{
						Type: graphql.Int,
					},
					"role": &graphql.ArgumentConfig{
						Type: graphql.String,
					},
				},
				Resolve: resolvers.GetUsers,
			},
			"organization": &graphql.Field{
				Type: organizationType,
				Args: graphql.FieldConfigArgument{
					"id": &graphql.ArgumentConfig{
						Type: graphql.NewNonNull(graphql.String),
					},
				},
				Resolve: resolvers.GetOrganization,
			},
			"organizations": &graphql.Field{
				Type: graphql.NewList(organizationType),
				Args: graphql.FieldConfigArgument{
					"limit": &graphql.ArgumentConfig{
						Type: graphql.Int,
					},
					"offset": &graphql.ArgumentConfig{
						Type: graphql.Int,
					},
				},
				Resolve: resolvers.GetOrganizations,
			},
		},
	})

	// Define mutation type
	mutationType := graphql.NewObject(graphql.ObjectConfig{
		Name: "Mutation",
		Fields: graphql.Fields{
			"createBuilding": &graphql.Field{
				Type: buildingType,
				Args: graphql.FieldConfigArgument{
					"input": &graphql.ArgumentConfig{
						Type: graphql.NewNonNull(createBuildingInput),
					},
				},
				Resolve: resolvers.CreateBuilding,
			},
			"updateBuilding": &graphql.Field{
				Type: buildingType,
				Args: graphql.FieldConfigArgument{
					"id": &graphql.ArgumentConfig{
						Type: graphql.NewNonNull(graphql.String),
					},
					"input": &graphql.ArgumentConfig{
						Type: graphql.NewNonNull(updateBuildingInput),
					},
				},
				Resolve: resolvers.UpdateBuilding,
			},
			"deleteBuilding": &graphql.Field{
				Type: graphql.Boolean,
				Args: graphql.FieldConfigArgument{
					"id": &graphql.ArgumentConfig{
						Type: graphql.NewNonNull(graphql.String),
					},
				},
				Resolve: resolvers.DeleteBuilding,
			},
			"createEquipment": &graphql.Field{
				Type: equipmentType,
				Args: graphql.FieldConfigArgument{
					"input": &graphql.ArgumentConfig{
						Type: graphql.NewNonNull(createEquipmentInput),
					},
				},
				Resolve: resolvers.CreateEquipment,
			},
			"updateEquipment": &graphql.Field{
				Type: equipmentType,
				Args: graphql.FieldConfigArgument{
					"id": &graphql.ArgumentConfig{
						Type: graphql.NewNonNull(graphql.String),
					},
					"input": &graphql.ArgumentConfig{
						Type: graphql.NewNonNull(updateEquipmentInput),
					},
				},
				Resolve: resolvers.UpdateEquipment,
			},
			"deleteEquipment": &graphql.Field{
				Type: graphql.Boolean,
				Args: graphql.FieldConfigArgument{
					"id": &graphql.ArgumentConfig{
						Type: graphql.NewNonNull(graphql.String),
					},
				},
				Resolve: resolvers.DeleteEquipment,
			},
			"createUser": &graphql.Field{
				Type: userType,
				Args: graphql.FieldConfigArgument{
					"input": &graphql.ArgumentConfig{
						Type: graphql.NewNonNull(createUserInput),
					},
				},
				Resolve: resolvers.CreateUser,
			},
			"updateUser": &graphql.Field{
				Type: userType,
				Args: graphql.FieldConfigArgument{
					"id": &graphql.ArgumentConfig{
						Type: graphql.NewNonNull(graphql.String),
					},
					"input": &graphql.ArgumentConfig{
						Type: graphql.NewNonNull(updateUserInput),
					},
				},
				Resolve: resolvers.UpdateUser,
			},
			"deleteUser": &graphql.Field{
				Type: graphql.Boolean,
				Args: graphql.FieldConfigArgument{
					"id": &graphql.ArgumentConfig{
						Type: graphql.NewNonNull(graphql.String),
					},
				},
				Resolve: resolvers.DeleteUser,
			},
		},
	})

	// Create schema
	schemaConfig := graphql.SchemaConfig{
		Query:    queryType,
		Mutation: mutationType,
	}

	graphqlSchema, err := graphql.NewSchema(schemaConfig)
	if err != nil {
		return nil, err
	}

	schema.schema = &graphqlSchema
	return schema, nil
}

// Execute executes a GraphQL query
func (s *Schema) Execute(query string, variables map[string]interface{}) *graphql.Result {
	return graphql.Do(graphql.Params{
		Schema:         *s.schema,
		RequestString:  query,
		VariableValues: variables,
	})
}

// getBuildingType returns the Building GraphQL type
func (s *Schema) getBuildingType() *graphql.Object {
	return graphql.NewObject(graphql.ObjectConfig{
		Name: "Building",
		Fields: graphql.Fields{
			"id": &graphql.Field{
				Type: graphql.String,
			},
			"name": &graphql.Field{
				Type: graphql.String,
			},
			"address": &graphql.Field{
				Type: graphql.String,
			},
			"latitude": &graphql.Field{
				Type: graphql.Float,
			},
			"longitude": &graphql.Field{
				Type: graphql.Float,
			},
			"createdAt": &graphql.Field{
				Type: graphql.DateTime,
			},
			"updatedAt": &graphql.Field{
				Type: graphql.DateTime,
			},
			"equipment": &graphql.Field{
				Type: graphql.NewList(s.getEquipmentType()),
				Resolve: func(p graphql.ResolveParams) (interface{}, error) {
					// This would resolve equipment for the building
					return []interface{}{}, nil
				},
			},
			"components": &graphql.Field{
				Type: graphql.NewList(s.getComponentType()),
				Resolve: func(p graphql.ResolveParams) (interface{}, error) {
					// This would resolve components for the building
					return []interface{}{}, nil
				},
			},
		},
	})
}

// getEquipmentType returns the Equipment GraphQL type
func (s *Schema) getEquipmentType() *graphql.Object {
	return graphql.NewObject(graphql.ObjectConfig{
		Name: "Equipment",
		Fields: graphql.Fields{
			"id": &graphql.Field{
				Type: graphql.String,
			},
			"name": &graphql.Field{
				Type: graphql.String,
			},
			"type": &graphql.Field{
				Type: graphql.String,
			},
			"status": &graphql.Field{
				Type: graphql.String,
			},
			"buildingId": &graphql.Field{
				Type: graphql.String,
			},
			"floorId": &graphql.Field{
				Type: graphql.String,
			},
			"roomId": &graphql.Field{
				Type: graphql.String,
			},
			"location": &graphql.Field{
				Type: graphql.String,
			},
			"createdAt": &graphql.Field{
				Type: graphql.DateTime,
			},
			"updatedAt": &graphql.Field{
				Type: graphql.DateTime,
			},
			"building": &graphql.Field{
				Type: s.getBuildingType(),
				Resolve: func(p graphql.ResolveParams) (interface{}, error) {
					// This would resolve the building for the equipment
					return nil, nil
				},
			},
		},
	})
}

// getComponentType returns the Component GraphQL type
func (s *Schema) getComponentType() *graphql.Object {
	return graphql.NewObject(graphql.ObjectConfig{
		Name: "Component",
		Fields: graphql.Fields{
			"id": &graphql.Field{
				Type: graphql.String,
			},
			"name": &graphql.Field{
				Type: graphql.String,
			},
			"type": &graphql.Field{
				Type: graphql.String,
			},
			"status": &graphql.Field{
				Type: graphql.String,
			},
			"path": &graphql.Field{
				Type: graphql.String,
			},
			"buildingId": &graphql.Field{
				Type: graphql.String,
			},
			"createdAt": &graphql.Field{
				Type: graphql.DateTime,
			},
			"updatedAt": &graphql.Field{
				Type: graphql.DateTime,
			},
		},
	})
}

// getUserType returns the User GraphQL type
func (s *Schema) getUserType() *graphql.Object {
	return graphql.NewObject(graphql.ObjectConfig{
		Name: "User",
		Fields: graphql.Fields{
			"id": &graphql.Field{
				Type: graphql.String,
			},
			"email": &graphql.Field{
				Type: graphql.String,
			},
			"name": &graphql.Field{
				Type: graphql.String,
			},
			"role": &graphql.Field{
				Type: graphql.String,
			},
			"active": &graphql.Field{
				Type: graphql.Boolean,
			},
			"organizationId": &graphql.Field{
				Type: graphql.String,
			},
			"createdAt": &graphql.Field{
				Type: graphql.DateTime,
			},
			"updatedAt": &graphql.Field{
				Type: graphql.DateTime,
			},
		},
	})
}

// getOrganizationType returns the Organization GraphQL type
func (s *Schema) getOrganizationType() *graphql.Object {
	return graphql.NewObject(graphql.ObjectConfig{
		Name: "Organization",
		Fields: graphql.Fields{
			"id": &graphql.Field{
				Type: graphql.String,
			},
			"name": &graphql.Field{
				Type: graphql.String,
			},
			"description": &graphql.Field{
				Type: graphql.String,
			},
			"plan": &graphql.Field{
				Type: graphql.String,
			},
			"active": &graphql.Field{
				Type: graphql.Boolean,
			},
			"createdAt": &graphql.Field{
				Type: graphql.DateTime,
			},
			"updatedAt": &graphql.Field{
				Type: graphql.DateTime,
			},
		},
	})
}

// getFloorType returns the Floor GraphQL type
func (s *Schema) getFloorType() *graphql.Object {
	return graphql.NewObject(graphql.ObjectConfig{
		Name: "Floor",
		Fields: graphql.Fields{
			"id": &graphql.Field{
				Type: graphql.String,
			},
			"name": &graphql.Field{
				Type: graphql.String,
			},
			"level": &graphql.Field{
				Type: graphql.Int,
			},
			"buildingId": &graphql.Field{
				Type: graphql.String,
			},
			"createdAt": &graphql.Field{
				Type: graphql.DateTime,
			},
			"updatedAt": &graphql.Field{
				Type: graphql.DateTime,
			},
		},
	})
}

// getRoomType returns the Room GraphQL type
func (s *Schema) getRoomType() *graphql.Object {
	return graphql.NewObject(graphql.ObjectConfig{
		Name: "Room",
		Fields: graphql.Fields{
			"id": &graphql.Field{
				Type: graphql.String,
			},
			"name": &graphql.Field{
				Type: graphql.String,
			},
			"type": &graphql.Field{
				Type: graphql.String,
			},
			"floorId": &graphql.Field{
				Type: graphql.String,
			},
			"createdAt": &graphql.Field{
				Type: graphql.DateTime,
			},
			"updatedAt": &graphql.Field{
				Type: graphql.DateTime,
			},
		},
	})
}

// Input types
func (s *Schema) getCreateBuildingInputType() *graphql.InputObject {
	return graphql.NewInputObject(graphql.InputObjectConfig{
		Name: "CreateBuildingInput",
		Fields: graphql.InputObjectConfigFieldMap{
			"name": &graphql.InputObjectFieldConfig{
				Type: graphql.NewNonNull(graphql.String),
			},
			"address": &graphql.InputObjectFieldConfig{
				Type: graphql.NewNonNull(graphql.String),
			},
			"latitude": &graphql.InputObjectFieldConfig{
				Type: graphql.Float,
			},
			"longitude": &graphql.InputObjectFieldConfig{
				Type: graphql.Float,
			},
		},
	})
}

func (s *Schema) getUpdateBuildingInputType() *graphql.InputObject {
	return graphql.NewInputObject(graphql.InputObjectConfig{
		Name: "UpdateBuildingInput",
		Fields: graphql.InputObjectConfigFieldMap{
			"name": &graphql.InputObjectFieldConfig{
				Type: graphql.String,
			},
			"address": &graphql.InputObjectFieldConfig{
				Type: graphql.String,
			},
			"latitude": &graphql.InputObjectFieldConfig{
				Type: graphql.Float,
			},
			"longitude": &graphql.InputObjectFieldConfig{
				Type: graphql.Float,
			},
		},
	})
}

func (s *Schema) getCreateEquipmentInputType() *graphql.InputObject {
	return graphql.NewInputObject(graphql.InputObjectConfig{
		Name: "CreateEquipmentInput",
		Fields: graphql.InputObjectConfigFieldMap{
			"name": &graphql.InputObjectFieldConfig{
				Type: graphql.NewNonNull(graphql.String),
			},
			"type": &graphql.InputObjectFieldConfig{
				Type: graphql.NewNonNull(graphql.String),
			},
			"buildingId": &graphql.InputObjectFieldConfig{
				Type: graphql.NewNonNull(graphql.String),
			},
			"floorId": &graphql.InputObjectFieldConfig{
				Type: graphql.String,
			},
			"roomId": &graphql.InputObjectFieldConfig{
				Type: graphql.String,
			},
			"location": &graphql.InputObjectFieldConfig{
				Type: graphql.String,
			},
		},
	})
}

func (s *Schema) getUpdateEquipmentInputType() *graphql.InputObject {
	return graphql.NewInputObject(graphql.InputObjectConfig{
		Name: "UpdateEquipmentInput",
		Fields: graphql.InputObjectConfigFieldMap{
			"name": &graphql.InputObjectFieldConfig{
				Type: graphql.String,
			},
			"type": &graphql.InputObjectFieldConfig{
				Type: graphql.String,
			},
			"status": &graphql.InputObjectFieldConfig{
				Type: graphql.String,
			},
			"floorId": &graphql.InputObjectFieldConfig{
				Type: graphql.String,
			},
			"roomId": &graphql.InputObjectFieldConfig{
				Type: graphql.String,
			},
			"location": &graphql.InputObjectFieldConfig{
				Type: graphql.String,
			},
		},
	})
}

func (s *Schema) getCreateUserInputType() *graphql.InputObject {
	return graphql.NewInputObject(graphql.InputObjectConfig{
		Name: "CreateUserInput",
		Fields: graphql.InputObjectConfigFieldMap{
			"email": &graphql.InputObjectFieldConfig{
				Type: graphql.NewNonNull(graphql.String),
			},
			"name": &graphql.InputObjectFieldConfig{
				Type: graphql.NewNonNull(graphql.String),
			},
			"password": &graphql.InputObjectFieldConfig{
				Type: graphql.NewNonNull(graphql.String),
			},
			"role": &graphql.InputObjectFieldConfig{
				Type: graphql.NewNonNull(graphql.String),
			},
			"organizationId": &graphql.InputObjectFieldConfig{
				Type: graphql.String,
			},
		},
	})
}

func (s *Schema) getUpdateUserInputType() *graphql.InputObject {
	return graphql.NewInputObject(graphql.InputObjectConfig{
		Name: "UpdateUserInput",
		Fields: graphql.InputObjectConfigFieldMap{
			"name": &graphql.InputObjectFieldConfig{
				Type: graphql.String,
			},
			"role": &graphql.InputObjectFieldConfig{
				Type: graphql.String,
			},
			"active": &graphql.InputObjectFieldConfig{
				Type: graphql.Boolean,
			},
		},
	})
}
