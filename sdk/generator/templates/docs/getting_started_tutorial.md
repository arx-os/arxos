# Getting Started with Arxos SDKs

Welcome to the Arxos SDK! This tutorial will guide you through setting up and using the SDK in your preferred programming language.

## 🎯 What You'll Learn

- Installing the SDK
- Setting up authentication
- Making your first API call
- Handling errors and responses
- Best practices for production use

## 📋 Prerequisites

Before you begin, make sure you have:

- A valid Arxos account
- API credentials (API key or username/password)
- {{ language.title() }} {{ min_version }} or higher
- Internet connection for API access

## 🚀 Quick Start

### Step 1: Install the SDK

Choose your preferred language:

{% for lang in languages %}
#### {{ lang.title() }}

```{{ lang }}
{{ installation_codes[lang] }}
```
{% endfor %}

### Step 2: Set Up Authentication

All Arxos SDKs support multiple authentication methods:

#### API Key Authentication (Recommended)

```{{ language }}
{{ api_key_setup_code }}
```

#### Username/Password Authentication

```{{ language }}
{{ username_password_setup_code }}
```

#### OAuth 2.0 Authentication

```{{ language }}
{{ oauth_setup_code }}
```

### Step 3: Make Your First API Call

Let's start with a simple health check:

```{{ language }}
{{ first_api_call_code }}
```

If everything is set up correctly, you should see:

```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0"
}
```

## 🏗️ Your First Project

Let's create a complete workflow to manage a building project:

### Step 1: Create a Project

```{{ language }}
{{ create_project_workflow_code }}
```

### Step 2: Add a Building

```{{ language }}
{{ add_building_workflow_code }}
```

### Step 3: Create BIM Objects

```{{ language }}
{{ create_bim_objects_workflow_code }}
```

### Step 4: Manage Assets

```{{ language }}
{{ manage_assets_workflow_code }}
```

## 🔧 Configuration Options

### Environment Variables

Set these environment variables for automatic configuration:

```bash
ARXOS_API_URL=https://api.arxos.com
ARXOS_API_KEY=your_api_key_here
ARXOS_LOG_LEVEL=info
ARXOS_TIMEOUT=30
```

### Custom Configuration

```{{ language }}
{{ custom_config_code }}
```

### Logging Configuration

```{{ language }}
{{ logging_config_code }}
```

## 🚨 Error Handling

### Basic Error Handling

```{{ language }}
{{ basic_error_handling_code }}
```

### Advanced Error Handling

```{{ language }}
{{ advanced_error_handling_code }}
```

### Retry Logic

```{{ language }}
{{ retry_logic_code }}
```

## 📊 Working with Data

### Pagination

```{{ language }}
{{ pagination_code }}
```

### Filtering and Search

```{{ language }}
{{ filtering_code }}
```

### Batch Operations

```{{ language }}
{{ batch_operations_code }}
```

## 🔄 Real-World Examples

### Complete Project Management

```{{ language }}
{{ complete_project_management_code }}
```

### Asset Inventory Management

```{{ language }}
{{ asset_inventory_management_code }}
```

### CMMS Integration

```{{ language }}
{{ cmms_integration_code }}
```

### SVG to BIM Conversion

```{{ language }}
{{ svg_to_bim_conversion_code }}
```

## 🧪 Testing Your Integration

### Unit Tests

```{{ language }}
{{ unit_tests_code }}
```

### Integration Tests

```{{ language }}
{{ integration_tests_code }}
```

### Mock Testing

```{{ language }}
{{ mock_testing_code }}
```

## 📈 Performance Optimization

### Connection Pooling

```{{ language }}
{{ connection_pooling_code }}
```

### Request Batching

```{{ language }}
{{ request_batching_code }}
```

### Caching

```{{ language }}
{{ caching_code }}
```

## 🔒 Security Best Practices

### Secure Configuration

```{{ language }}
{{ secure_config_code }}
```

### Input Validation

```{{ language }}
{{ input_validation_code }}
```

### Certificate Validation

```{{ language }}
{{ certificate_validation_code }}
```

## 🚀 Production Deployment

### Environment Setup

```{{ language }}
{{ production_env_setup_code }}
```

### Monitoring and Logging

```{{ language }}
{{ monitoring_logging_code }}
```

### Error Tracking

```{{ language }}
{{ error_tracking_code }}
```

## 📚 Next Steps

Now that you have the basics, explore these resources:

### Documentation
- [API Reference](../api_reference.md)
- [Examples](../examples/)
- [Tutorials](../tutorials/)

### Advanced Topics
- [Authentication Tutorial](authentication_tutorial.md)
- [API Integration Tutorial](api_integration_tutorial.md)
- [Best Practices Tutorial](best_practices_tutorial.md)

### Community
- [GitHub Repository](https://github.com/arxos/sdk)
- [Issues & Discussions](https://github.com/arxos/sdk/discussions)
- [Support Documentation](https://docs.arxos.com)

## 🆘 Getting Help

### Common Issues

#### Authentication Errors
```{{ language }}
{{ auth_error_troubleshooting_code }}
```

#### Network Issues
```{{ language }}
{{ network_troubleshooting_code }}
```

#### Rate Limiting
```{{ language }}
{{ rate_limit_troubleshooting_code }}
```

### Support Channels

- **Documentation**: [https://docs.arxos.com](https://docs.arxos.com)
- **API Reference**: [https://api.arxos.com/docs](https://api.arxos.com/docs)
- **GitHub Issues**: [https://github.com/arxos/sdk/issues](https://github.com/arxos/sdk/issues)
- **Community**: [https://github.com/arxos/sdk/discussions](https://github.com/arxos/sdk/discussions)

## 🎉 Congratulations!

You've successfully set up the Arxos SDK and made your first API calls. You're now ready to build powerful applications that integrate with the Arxos platform.

### What's Next?

1. **Explore the API**: Try different endpoints and see what data is available
2. **Build Your Application**: Use the SDK to create your own applications
3. **Join the Community**: Share your projects and get help from other developers
4. **Contribute**: Help improve the SDK by contributing code or documentation

Happy coding! 🚀
