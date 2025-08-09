#!/bin/bash

# Arxos Kubernetes Deployment Validation Script
# This script validates the Kubernetes deployment configuration for 100% compliance

set -e

echo "🔍 Validating Arxos Kubernetes deployment configuration..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a condition is met
check() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
        exit 1
    fi
}

# Function to check namespace consistency
check_namespace() {
    local file=$1
    local expected_namespace=$2
    local actual_namespace=$(grep -h "namespace:" "$file" | head -1 | awk '{print $2}')

    if [ "$actual_namespace" = "$expected_namespace" ]; then
        echo -e "${GREEN}✅ $file uses correct namespace: $expected_namespace${NC}"
    else
        echo -e "${RED}❌ $file uses wrong namespace: $actual_namespace (expected: $expected_namespace)${NC}"
        return 1
    fi
}

# Check if all required files exist
echo "📁 Checking file structure..."

required_files=(
    "namespaces.yaml"
    "svgx-engine.yaml"
    "export-service.yaml"
    "ingress.yaml"
    "monitoring.yaml"
    "README.md"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $file exists${NC}"
    else
        echo -e "${RED}❌ $file missing${NC}"
        exit 1
    fi
done

# Check environment files
echo "🌍 Checking environment files..."
env_files=(
    "environments/production.yaml"
    "environments/production-svgx.yaml"
    "environments/staging.yaml"
    "environments/dev.yaml"
)

for file in "${env_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $file exists${NC}"
    else
        echo -e "${YELLOW}⚠️  $file missing (optional)${NC}"
    fi
done

# Check namespace consistency
echo "🏷️  Checking namespace consistency..."

# Main files should use 'arxos' namespace
main_files=(
    "svgx-engine.yaml"
    "export-service.yaml"
    "ingress.yaml"
    "monitoring.yaml"
)

for file in "${main_files[@]}"; do
    check_namespace "$file" "arxos"
done

# Check for any remaining 'svgx' namespace references
echo "🔍 Checking for old namespace references..."
svgx_namespace_count=$(grep -r "namespace: svgx" . --include="*.yaml" | wc -l)
if [ "$svgx_namespace_count" -eq 0 ]; then
    echo -e "${GREEN}✅ No old 'svgx' namespace references found${NC}"
else
    echo -e "${RED}❌ Found $svgx_namespace_count old 'svgx' namespace references${NC}"
    grep -r "namespace: svgx" . --include="*.yaml"
    exit 1
fi

# Check for service definitions
echo "🔗 Checking service definitions..."
svgx_service_count=$(grep -c "kind: Service" svgx-engine.yaml)
export_service_count=$(grep -c "kind: Service" export-service.yaml)

if [ "$svgx_service_count" -gt 0 ]; then
    echo -e "${GREEN}✅ SVGX Engine has service definition${NC}"
else
    echo -e "${RED}❌ SVGX Engine missing service definition${NC}"
    exit 1
fi

if [ "$export_service_count" -gt 0 ]; then
    echo -e "${GREEN}✅ Export Service has service definition${NC}"
else
    echo -e "${RED}❌ Export Service missing service definition${NC}"
    exit 1
fi

# Check for HPA definitions
echo "📈 Checking HPA definitions..."
svgx_hpa_count=$(grep -c "kind: HorizontalPodAutoscaler" svgx-engine.yaml)
export_hpa_count=$(grep -c "kind: HorizontalPodAutoscaler" export-service.yaml)

if [ "$svgx_hpa_count" -gt 0 ]; then
    echo -e "${GREEN}✅ SVGX Engine has HPA definition${NC}"
else
    echo -e "${RED}❌ SVGX Engine missing HPA definition${NC}"
    exit 1
fi

if [ "$export_hpa_count" -gt 0 ]; then
    echo -e "${GREEN}✅ Export Service has HPA definition${NC}"
else
    echo -e "${RED}❌ Export Service missing HPA definition${NC}"
    exit 1
fi

# Check for RBAC definitions
echo "🔐 Checking RBAC definitions..."
svgx_rbac_count=$(grep -c "kind: Role\|kind: RoleBinding" svgx-engine.yaml)
export_rbac_count=$(grep -c "kind: Role\|kind: RoleBinding" export-service.yaml)

if [ "$svgx_rbac_count" -gt 0 ]; then
    echo -e "${GREEN}✅ SVGX Engine has RBAC definitions${NC}"
else
    echo -e "${RED}❌ SVGX Engine missing RBAC definitions${NC}"
    exit 1
fi

if [ "$export_rbac_count" -gt 0 ]; then
    echo -e "${GREEN}✅ Export Service has RBAC definitions${NC}"
else
    echo -e "${RED}❌ Export Service missing RBAC definitions${NC}"
    exit 1
fi

# Check for monitoring configuration
echo "📊 Checking monitoring configuration..."
monitoring_count=$(grep -c "kind: ServiceMonitor\|kind: PrometheusRule" monitoring.yaml)
if [ "$monitoring_count" -gt 0 ]; then
    echo -e "${GREEN}✅ Monitoring configuration present${NC}"
else
    echo -e "${RED}❌ Monitoring configuration missing${NC}"
    exit 1
fi

# Check for ingress configuration
echo "🌐 Checking ingress configuration..."
ingress_count=$(grep -c "kind: Ingress" ingress.yaml)
if [ "$ingress_count" -gt 0 ]; then
    echo -e "${GREEN}✅ Ingress configuration present${NC}"
else
    echo -e "${RED}❌ Ingress configuration missing${NC}"
    exit 1
fi

# Check for security context
echo "🔒 Checking security context..."
security_context_count=$(grep -c "securityContext" svgx-engine.yaml)
if [ "$security_context_count" -gt 0 ]; then
    echo -e "${GREEN}✅ Security context configured${NC}"
else
    echo -e "${RED}❌ Security context missing${NC}"
    exit 1
fi

# Check for resource limits
echo "💾 Checking resource limits..."
resource_limits_count=$(grep -c "resources:" svgx-engine.yaml)
if [ "$resource_limits_count" -gt 0 ]; then
    echo -e "${GREEN}✅ Resource limits configured${NC}"
else
    echo -e "${RED}❌ Resource limits missing${NC}"
    exit 1
fi

# Check for health checks
echo "🏥 Checking health checks..."
health_check_count=$(grep -c "livenessProbe\|readinessProbe" svgx-engine.yaml)
if [ "$health_check_count" -gt 0 ]; then
    echo -e "${GREEN}✅ Health checks configured${NC}"
else
    echo -e "${RED}❌ Health checks missing${NC}"
    exit 1
fi

# Validate YAML syntax
echo "📝 Validating YAML syntax..."
for file in *.yaml; do
    if [ -f "$file" ]; then
        if kubectl apply --dry-run=client -f "$file" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ $file has valid YAML syntax${NC}"
        else
            echo -e "${RED}❌ $file has invalid YAML syntax${NC}"
            exit 1
        fi
    fi
done

echo ""
echo -e "${GREEN}🎉 All validation checks passed! The Kubernetes deployment is 100% compliant.${NC}"
echo ""
echo "📋 Summary:"
echo "✅ All required files present"
echo "✅ Namespace consistency verified"
echo "✅ Service definitions present"
echo "✅ HPA configurations present"
echo "✅ RBAC configurations present"
echo "✅ Monitoring configuration present"
echo "✅ Ingress configuration present"
echo "✅ Security context configured"
echo "✅ Resource limits configured"
echo "✅ Health checks configured"
echo "✅ YAML syntax validated"
echo ""
echo "🚀 Ready for deployment!"
